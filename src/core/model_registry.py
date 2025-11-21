"""Model Registry - Central governance and version control for ML models"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
import pickle

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for model registration"""
    name: str
    version: str
    model_type: str  # classifier, regressor, embedder
    domain: str  # credit, fraud, capacity
    created_date: str
    created_by: str
    approval_date: Optional[str] = None
    approved_by: Optional[str] = None
    status: str = 'development'  # development, approved, production, deprecated
    performance_metrics: Optional[Dict[str, float]] = None
    validation_report: Optional[str] = None
    data_sha256: Optional[str] = None
    model_sha256: Optional[str] = None


class ModelRegistry:
    """
    Central registry for model governance, versioning, and lineage tracking
    Supports MLflow backend or filesystem-based storage
    """
    
    def __init__(self, backend: str = 'mlflow', uri: str = 'mlruns/'):
        """
        Initialize model registry
        
        Args:
            backend: 'mlflow' or 'filesystem'
            uri: MLflow tracking URI or filesystem path
        """
        self.backend = backend
        self.uri = uri
        self.models: Dict[str, List[ModelMetadata]] = {}
        
        if backend == 'filesystem':
            self.storage_path = Path(uri)
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._load_registry()
    
    def register(
        self,
        name: str,
        model: Any,
        model_type: str,
        created_by: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelMetadata:
        """
        Register a new model version
        
        Args:
            name: Model name (e.g., 'credit_scoring')
            model: Trained model object (sklearn, XGBoost, etc.)
            model_type: 'classifier' or 'regressor'
            created_by: User/team registering model
            metadata: Additional metadata dict
        
        Returns:
            ModelMetadata with registration info
        """
        try:
            # Generate version tag
            current_version = len(self.models.get(name, [])) + 1
            version_tag = f"v{current_version}.0"
            
            # Calculate model hash
            model_sha = self._calculate_sha256(model)
            
            # Create metadata
            model_meta = ModelMetadata(
                name=name,
                version=version_tag,
                model_type=model_type,
                domain=metadata.get('domain', 'general') if metadata else 'general',
                created_date=datetime.now().isoformat(),
                created_by=created_by,
                approval_date=metadata.get('approval_date') if metadata else None,
                approved_by=metadata.get('approved_by') if metadata else None,
                status=metadata.get('status', 'development') if metadata else 'development',
                performance_metrics=metadata.get('performance_metrics') if metadata else None,
                model_sha256=model_sha
            )
            
            # Store model
            if self.backend == 'filesystem':
                self._save_model_filesystem(name, version_tag, model, model_meta)
            elif self.backend == 'mlflow':
                self._save_model_mlflow(name, version_tag, model, model_meta)
            
            # Update registry
            if name not in self.models:
                self.models[name] = []
            self.models[name].append(model_meta)
            
            logger.info(f"✓ Registered {name}:{version_tag} by {created_by}")
            return model_meta
            
        except Exception as e:
            logger.error(f"Failed to register model {name}: {str(e)}")
            raise
    
    def get_production_model(self, name: str) -> Optional[Dict[str, Any]]:
        """Get current production model version"""
        if name not in self.models:
            logger.warning(f"Model {name} not found in registry")
            return None
        
        # Find latest production version
        versions = self.models[name]
        prod_versions = [v for v in versions if v.status == 'production']
        
        if not prod_versions:
            logger.warning(f"No production version for {name}")
            return None
        
        latest = max(prod_versions, key=lambda x: x.created_date)
        return {
            'metadata': latest,
            'model': self._load_model(name, latest.version)
        }
    
    def get_model_version(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get specific model version"""
        if name not in self.models:
            return None
        
        metadata_list = [v for v in self.models[name] if v.version == version]
        if not metadata_list:
            return None
        
        return {
            'metadata': metadata_list[0],
            'model': self._load_model(name, version)
        }
    
    def list_models(self, filters: Optional[Dict[str, str]] = None) -> List[ModelMetadata]:
        """List models with optional filtering"""
        all_models = []
        for versions in self.models.values():
            all_models.extend(versions)
        
        if not filters:
            return all_models
        
        # Apply filters
        filtered = all_models
        if 'domain' in filters:
            filtered = [m for m in filtered if m.domain == filters['domain']]
        if 'status' in filters:
            filtered = [m for m in filtered if m.status == filters['status']]
        
        return filtered
    
    def promote_to_production(
        self,
        name: str,
        version: str,
        approved_by: str,
        approval_notes: str
    ) -> bool:
        """Promote model version to production"""
        try:
            if name not in self.models:
                logger.error(f"Model {name} not found")
                return False
            
            # Find version
            version_meta = None
            for vm in self.models[name]:
                if vm.version == version:
                    version_meta = vm
                    break
            
            if not version_meta:
                logger.error(f"Version {version} not found for {name}")
                return False
            
            # Demote current production
            for vm in self.models[name]:
                if vm.status == 'production':
                    vm.status = 'staging'
            
            # Promote new version
            version_meta.status = 'production'
            version_meta.approved_by = approved_by
            version_meta.approval_date = datetime.now().isoformat()
            
            logger.info(f"✓ Promoted {name}:{version} to production")
            return True
            
        except Exception as e:
            logger.error(f"Failed to promote model: {str(e)}")
            return False
    
    @staticmethod
    def _calculate_sha256(obj: Any) -> str:
        """Calculate SHA256 hash of object"""
        serialized = pickle.dumps(obj)
        return hashlib.sha256(serialized).hexdigest()
    
    def _save_model_filesystem(
        self,
        name: str,
        version: str,
        model: Any,
        metadata: ModelMetadata
    ):
        """Save model to filesystem"""
        model_dir = self.storage_path / name / version
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model
        with open(model_dir / 'model.pkl', 'wb') as f:
            pickle.dump(model, f)
        
        # Save metadata
        with open(model_dir / 'metadata.json', 'w') as f:
            json.dump(asdict(metadata), f, indent=2, default=str)
    
    def _load_model(self, name: str, version: str) -> Any:
        """Load model from storage"""
        model_path = self.storage_path / name / version / 'model.pkl'
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    
    def _save_model_mlflow(self, name: str, version: str, model: Any, metadata: ModelMetadata):
        """Save model to MLflow (implementation)"""
        # In production, this would use mlflow.sklearn.log_model() or similar
        pass
    
    def _load_registry(self):
        """Load existing registry from filesystem"""
        for model_dir in self.storage_path.iterdir():
            if model_dir.is_dir():
                for version_dir in model_dir.iterdir():
                    if version_dir.is_dir():
                        metadata_file = version_dir / 'metadata.json'
                        if metadata_file.exists():
                            with open(metadata_file, 'r') as f:
                                meta_dict = json.load(f)
                                meta = ModelMetadata(**meta_dict)
                                if model_dir.name not in self.models:
                                    self.models[model_dir.name] = []
                                self.models[model_dir.name].append(meta)


class AuditTrail:
    """Audit trail logging for compliance and governance"""
    
    def __init__(self, storage: str = 'filesystem', path: str = 'audit_logs/'):
        self.storage = storage
        self.path = Path(path) if storage == 'filesystem' else path
        if storage == 'filesystem':
            self.path.mkdir(parents=True, exist_ok=True)
        self.logs: List[Dict[str, Any]] = []
    
    def log_action(
        self,
        action: str,
        model_id: str,
        actor: str,
        details: Dict[str, Any],
        status: str = 'SUCCESS'
    ) -> bool:
        """Log an action for audit trail"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'model_id': model_id,
                'actor': actor,
                'details': details,
                'status': status
            }
            
            self.logs.append(log_entry)
            
            if self.storage == 'filesystem':
                self._save_log_filesystem(log_entry)
            
            logger.info(f"✓ Audit log: {action} on {model_id} by {actor}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit trail: {str(e)}")
            return False
    
    def _save_log_filesystem(self, log_entry: Dict[str, Any]):
        """Save log entry to filesystem"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = self.path / f"audit_{date_str}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_logs(
        self,
        model_id: Optional[str] = None,
        action: Optional[str] = None,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Query audit logs"""
        filtered = self.logs
        
        if model_id:
            filtered = [l for l in filtered if l['model_id'] == model_id]
        if action:
            filtered = [l for l in filtered if l['action'] == action]
        
        return filtered
