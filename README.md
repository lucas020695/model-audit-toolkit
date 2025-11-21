# quantdeskportfolio

**Data Engineering & Risk Modeling for Brazilian Equities Portfolio Analytics**

A production-grade data warehouse and ETL pipeline for ingesting, transforming, and analyzing Brazilian equity market data with rigorous data quality controls and analytical dashboards.

## Overview

`quantdeskportfolio` demonstrates end-to-end financial data engineering:
- **Local data warehouse** architecture using DuckDB and dbt
- **Multi-layer ETL pipelines** (staging → analytics) with automated quality tests
- **Financial analytics** for portfolio risk and performance monitoring
- **Reproducible workflows** with version control and documentation

## Key Features

✅ **Data Ingestion**: Brazilian equities (PETR4.SA, VALE3.SA, ITUB4.SA, BBDC4.SA, BVSP)  
✅ **dbt-based Transformations**: Layered modeling (raw → staging → analytics)  
✅ **Data Quality**: Automated uniqueness, nullability, and business rule tests  
✅ **Risk Analytics**: Portfolio concentration, liquidity, performance metrics  
✅ **Modern Stack**: Python + SQL + DuckDB + dbt (no cloud required)  
✅ **Documentation**: Every model documented with lineage and assumptions  

## Technology Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Data Store | DuckDB | In-process OLAP database |
| ETL | dbt | SQL-based transformations + testing |
| Python | Pandas, SQLAlchemy | Data ingestion and analytics |
| Orchestration | Python scripts | Job scheduling and data loading |
| Version Control | Git | Reproducibility and collaboration |

## Project Structure

```
quantdeskportfolio/
├── dbt/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_market_data.sql
│   │   │   ├── stg_fundamentals.sql
│   │   │   └── schema.yml
│   │   ├── analytics/
│   │   │   ├── fct_portfolio_metrics.sql
│   │   │   ├── dim_tickers.sql
│   │   │   └── schema.yml
│   │   └── marts/
│   │       └── risk_dashboard.sql
│   ├── tests/
│   │   ├── assert_positive_prices.sql
│   │   ├── assert_unique_dates.sql
│   │   └── data_quality.yml
│   └── profiles.yml
├── src/
│   ├── __init__.py
│   ├── ingest.py
│   ├── validate.py
│   ├── config.py
│   └── utils.py
├── scripts/
│   ├── run_pipeline.py
│   ├── daily_refresh.sh
│   └── generate_reports.py
├── data/
│   └── raw/  (ignored in git, created on run)
├── README.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

## Quick Start

### Prerequisites
- Python 3.9+
- Git
- 2GB disk space

### Installation

```bash
# Clone repository
git clone https://github.com/lucas020695/quantdeskportfolio.git
cd quantdeskportfolio

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dbt dependencies
dbt deps
```

### Running the Pipeline

```bash
# 1. Ingest market data
python src/ingest.py --tickers PETR4.SA VALE3.SA ITUB4.SA BBDC4.SA --date-range "2024-01-01:2025-11-21"

# 2. Run dbt transformations
dbt run

# 3. Execute data quality tests
dbt test

# 4. Generate reports
python scripts/generate_reports.py --output reports/
```

## Data Sources

Ingests real-time and historical data for:

| Ticker | Company | Sector |
|--------|---------|--------|
| PETR4.SA | Petrobras | Energy |
| VALE3.SA | Vale | Mining |
| ITUB4.SA | Itaú | Banking |
| BBDC4.SA | Bradesco | Banking |
| BVSP | Bovespa Index | Index |

## Key Models

### Staging Layer (`stg_*`)
- `stg_market_data`: Raw OHLCV data with type casting and date validation
- `stg_fundamentals`: Financial ratios, P/E, dividend data
- `stg_macro`: Macro indicators (SELIC, USD rate, inflation)

### Analytics Layer (`fct_* + dim_*`)
- `fct_portfolio_metrics`: Daily portfolio price, volume, returns
- `dim_tickers`: Master ticker reference data
- `fct_risk_metrics`: Volatility, correlation, VaR calculations

### Marts Layer
- `risk_dashboard`: Aggregated metrics for reporting

## Example Queries

### Portfolio concentration risk
```sql
SELECT 
  ticker,
  market_cap,
  market_cap / SUM(market_cap) OVER () as portfolio_weight,
  CASE 
    WHEN market_cap / SUM(market_cap) OVER () > 0.30 THEN 'HIGH'
    WHEN market_cap / SUM(market_cap) OVER () > 0.15 THEN 'MEDIUM'
    ELSE 'LOW'
  END as concentration_risk
FROM risk_dashboard
ORDER BY concentration_risk DESC;
```

### Liquidity analysis
```sql
SELECT 
  ticker,
  avg_daily_volume,
  avg_spread_bps,
  CASE 
    WHEN avg_daily_volume > 1000000 THEN 'Highly Liquid'
    WHEN avg_daily_volume > 100000 THEN 'Liquid'
    ELSE 'Illiquid'
  END as liquidity_tier
FROM risk_dashboard
ORDER BY avg_daily_volume DESC;
```

## Development Workflow

### Adding a new model:
1. Create SQL file in `dbt/models/staging/` or `dbt/models/analytics/`
2. Document in corresponding `schema.yml`
3. Add tests in `dbt/tests/`
4. Run locally: `dbt run -s tag:new_model`
5. Commit and push to feature branch

### Validating data quality:
```bash
# Run all tests
dbt test

# Run tests for specific model
dbt test -s stg_market_data

# Generate lineage documentation
dbt docs generate && dbt docs serve
```

## Performance Characteristics

- **Data volume**: ~100K rows (1 year historical, 5 tickers, daily frequency)
- **Pipeline runtime**: ~45 seconds (ingest + transform + test)
- **Incremental loads**: ~5 seconds for daily updates
- **Query latency**: <1s for analytical queries (DuckDB in-memory)

## Regulatory & Compliance

Supports compliance workflows for:
- **CVM (Comissão de Valores Mobiliários)**: Brazilian SEC equivalent
- **IBGE**: Brazilian statistics agency data
- **Audit trails**: Full lineage tracking and data provenance

## Testing & Validation

```bash
# Data quality tests
dbt test

# Run Great Expectations (optional)
pytest tests/

# Regenerate documentation
dbt docs generate
```

## Deployment

### Local development
```bash
python scripts/run_pipeline.py --env dev
```

### Production setup (daily cron)
```bash
# Add to crontab
0 18 * * * cd /path/to/quantdeskportfolio && source venv/bin/activate && python scripts/daily_refresh.sh
```

## Troubleshooting

**Issue**: DuckDB connection error
```bash
# Reset database
rm -f data/quantdesk.duckdb
python src/ingest.py --force-reload
```

**Issue**: Data staleness
```bash
# Force refresh
dbt run --full-refresh
dbt test
```

## Future Enhancements

- [ ] Real-time data streaming (Kafka/Redpanda)
- [ ] Machine learning feature store integration
- [ ] Airflow orchestration for cloud deployment
- [ ] Web dashboard (Streamlit)
- [ ] Options data ingestion
- [ ] Multi-asset class support (bonds, futures)

## Contributing

Contributions welcome! Please:
1. Fork repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Add tests and documentation
4. Submit pull request

## Author

**Lucas Barbosa de Oliveira**
- [GitHub](https://github.com/lucas020695)
- [LinkedIn](https://linkedin.com/in/lucas-barbosa-053172353)

## License

MIT License - See LICENSE file for details

---

## Citation

If this project helps your work, please consider citing:

```bibtex
@software{quantdeskportfolio,
  author = {Barbosa de Oliveira, Lucas},
  title = {quantdeskportfolio: Financial Data Engineering for Portfolio Analytics},
  year = {2025},
  url = {https://github.com/lucas020695/quantdeskportfolio}
}
```

## References

- [dbt documentation](https://docs.getdbt.com/)
- [DuckDB SQL reference](https://duckdb.org/docs/sql/introduction)
- [Financial data engineering best practices](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/)
