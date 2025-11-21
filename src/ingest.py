import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    """Configuration management for data pipeline"""
    
    # Data paths
    DATA_DIR = Path(__file__).parent.parent / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    DB_PATH = DATA_DIR / "quantdesk.duckdb"
    
    # Data parameters
    TICKERS = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BVSP"]
    LOOKBACK_DAYS = 252  # 1 year of trading data
    
    # Validation rules
    MIN_VOLUME = 1000
    MAX_PRICE_CHANGE_PCT = 50
    MIN_VOLUME_MA20 = 500
    
    def __init__(self):
        self.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Config initialized. Data dir: {self.DATA_DIR}")


class DataValidator:
    """Validates data quality and business rules"""
    
    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> tuple[bool, List[str]]:
        """Validate OHLCV data structure and business rules"""
        issues = []
        
        # Schema validation
        required_cols = ['open', 'high', 'low', 'close', 'volume', 'date']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            issues.append(f"Missing columns: {missing}")
            return False, issues
        
        # Type validation
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if not pd.api.types.is_numeric_dtype(df[col]):
                issues.append(f"Column {col} is not numeric")
        
        # Business rule: OHLC ordering
        invalid_ohlc = df[(df['open'] < 0) | 
                          (df['high'] < df['low']) | 
                          (df['close'] < 0) | 
                          (df['volume'] < 0)]
        if not invalid_ohlc.empty:
            issues.append(f"{len(invalid_ohlc)} rows fail OHLC ordering rules")
        
        # Business rule: Price gaps (sanity check)
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            df[f'{col}_pct_change'] = df[col].pct_change().abs() * 100
            extreme_moves = df[df[f'{col}_pct_change'] > Config.MAX_PRICE_CHANGE_PCT]
            if not extreme_moves.empty:
                issues.append(f"{len(extreme_moves)} extreme price moves in {col}")
        
        # Null checks
        null_counts = df[numeric_cols].isnull().sum()
        if null_counts.sum() > 0:
            issues.append(f"Nulls found: {null_counts[null_counts > 0].to_dict()}")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_dates(df: pd.DataFrame) -> tuple[bool, List[str]]:
        """Validate date consistency"""
        issues = []
        
        # Check duplicates
        if df['date'].duplicated().any():
            issues.append(f"{df['date'].duplicated().sum()} duplicate dates")
        
        # Check ordering
        if not df['date'].is_monotonic_increasing:
            issues.append("Dates not in ascending order")
        
        # Check for future dates
        if (df['date'] > datetime.now().date()).any():
            issues.append("Future dates detected")
        
        return len(issues) == 0, issues


class MarketDataIngester:
    """Ingests market data from various sources"""
    
    @staticmethod
    def generate_synthetic_data(ticker: str, days: int = 252) -> pd.DataFrame:
        """
        Generate realistic synthetic OHLCV data for development/testing
        In production, this would fetch from Bloomberg, Yahoo Finance, etc.
        """
        np.random.seed(hash(ticker) % 2**32)
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
        
        # Generate realistic price series
        returns = np.random.normal(0.0003, 0.015, days)
        close_prices = 100 * np.exp(np.cumsum(returns))
        
        open_prices = close_prices * (1 + np.random.normal(0, 0.005, days))
        high_prices = np.maximum(open_prices, close_prices) * (1 + np.abs(np.random.normal(0, 0.01, days)))
        low_prices = np.minimum(open_prices, close_prices) * (1 - np.abs(np.random.normal(0, 0.01, days)))
        
        volumes = np.random.lognormal(14, 1, days).astype(int)
        
        df = pd.DataFrame({
            'date': dates.date,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes,
            'ticker': ticker,
            'ingestion_timestamp': datetime.now()
        })
        
        return df.reset_index(drop=True)
    
    @staticmethod
    def ingest(ticker: str, days: int = 252) -> Optional[pd.DataFrame]:
        """Ingest market data for a ticker"""
        try:
            logger.info(f"Ingesting data for {ticker} (last {days} days)")
            
            # In production: connect to Bloomberg, Yahoo Finance API, etc.
            # For now: synthetic data
            df = MarketDataIngester.generate_synthetic_data(ticker, days)
            
            # Validate
            valid, issues = DataValidator.validate_ohlcv(df)
            if not valid:
                logger.warning(f"Validation issues for {ticker}: {issues}")
            
            valid_dates, date_issues = DataValidator.validate_dates(df)
            if not valid_dates:
                logger.warning(f"Date issues for {ticker}: {date_issues}")
            
            logger.info(f"Successfully ingested {len(df)} records for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to ingest {ticker}: {str(e)}")
            return None


class PortfolioAnalytics:
    """Calculate portfolio metrics and risk analytics"""
    
    @staticmethod
    def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily returns and log returns"""
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        return df
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Calculate rolling volatility"""
        df[f'volatility_{window}d'] = df['returns'].rolling(window).std() * np.sqrt(252)
        return df
    
    @staticmethod
    def calculate_volume_metrics(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Calculate volume-related metrics"""
        df[f'avg_volume_{window}d'] = df['volume'].rolling(window).mean()
        df['volume_trend'] = df['volume'] / df[f'avg_volume_{window}d']
        return df
    
    @staticmethod
    def calculate_liquidity_spread(df: pd.DataFrame) -> pd.DataFrame:
        """Estimate bid-ask spread from OHLC data"""
        # Simplified: assumes typical spread patterns
        df['high_low_spread_bps'] = ((df['high'] - df['low']) / df['close'] * 10000)
        return df


class Pipeline:
    """Main ETL pipeline orchestrator"""
    
    def __init__(self, config: Config):
        self.config = config
        self.ingester = MarketDataIngester()
        self.validator = DataValidator()
        self.analytics = PortfolioAnalytics()
    
    def run_full_refresh(self, tickers: Optional[List[str]] = None) -> bool:
        """Execute full pipeline refresh"""
        tickers = tickers or self.config.TICKERS
        logger.info(f"Starting full pipeline refresh for {len(tickers)} tickers")
        
        all_data = []
        
        for ticker in tickers:
            # Ingest
            df = self.ingester.ingest(ticker, self.config.LOOKBACK_DAYS)
            if df is None:
                continue
            
            # Enrich
            df = self.analytics.calculate_returns(df)
            df = self.analytics.calculate_volatility(df)
            df = self.analytics.calculate_volume_metrics(df)
            df = self.analytics.calculate_liquidity_spread(df)
            
            all_data.append(df)
        
        if not all_data:
            logger.error("No data ingested from any ticker")
            return False
        
        # Combine and save
        combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"Pipeline complete: {len(combined)} total rows ingested")
        
        return True


if __name__ == "__main__":
    config = Config()
    pipeline = Pipeline(config)
    success = pipeline.run_full_refresh()
    sys.exit(0 if success else 1)
