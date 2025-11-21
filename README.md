# model-audit-toolkit

**Model Risk Management & Compliance Automation Platform**

A comprehensive Python framework for automated validation, monitoring, and explainability of critical machine learning models (credit scoring, fraud detection, capacity models) with regulatory compliance (BCBS 239, IFRS) logging.

## Overview

`model-audit-toolkit` enables financial institutions to:
- **Validate** models against regulatory requirements and business rules
- **Detect drift** and performance degradation in production models
- **Explain** model predictions with SHAP/LIME for audit trails
- **Automate** compliance reporting for regulators (BCBS 239)
- **Track lineage** and version control for model governance

## Key Features

✅ **Automated Model Validation**: Independent comparison against baseline/holdout sets  
✅ **Drift Detection**: Statistical monitoring for data/model performance drift  
✅ **Model Explainability**: SHAP/LIME integration for decision transparency  
✅ **Regulatory Compliance**: BCBS 239, IFRS logging and audit trails  
✅ **Multi-Model Support**: Credit scoring, fraud, capacity, bespoke models  
✅ **CICD Integration**: Git-based versioning, automated testing pipelines  
✅ **Production-Ready**: MLflow tracking, remote logging, alerting  

## Technology Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Model Tracking | MLflow | Experiment tracking & model registry |
| Explainability | SHAP, LIME | Feature importance & local explanations |
| Validation | pytest, Great Expectations | Data quality & model testing |
| Compliance | Custom logging | BCBS 239 audit trails |
| Version Control | Git | Reproducibility & governance |
| Environment | Poetry/pip | Dependency management |

## Project Structure

```
model-audit-toolkit/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── model_registry.py
│   │   ├── validator.py
│   │   ├── drift_detector.py
│   │   └── explainer.py
│   ├── compliance/
│   │   ├── bcbs239_logger.py
│   │   ├── audit_trail.py
│   │   └── reporting.py
│   ├── utils/
│   │   ├── data_utils.py
│   │   ├── metrics.py
│   │   └── helpers.py
│   └── config.py
├── tests/
│   ├── test_validator.py
│   ├── test_drift_detector.py
│   ├── test_explainer.py
│   └── test_compliance.py
├── examples/
│   ├── credit_score_validation.py
│   ├── fraud_detection_monitoring.py
│   └── capacity_model_audit.py
├── .github/workflows/
│   ├── ci_cd.yml
│   └── model_tests.yml
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── LICENSE
```

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/lucas020695/model-audit-toolkit.git
cd model-audit-toolkit

# Create environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "from src.core.model_registry import ModelRegistry; print('✓ Installation successful')"
```

### Basic Usage

#### 1. Register and validate a model

```python
from src.core.model_registry import ModelRegistry
from src.core.validator import ModelValidator

# Initialize registry
registry = ModelRegistry(backend='mlflow', uri='mlruns/')

# Register model
model_info = registry.register(
    name='credit_scoring_v2.1',
    model=trained_model,
    model_type='classifier',
    metadata={
        'domain': 'credit',
        'approval_date': '2025-11-21',
        'model_owner': 'risk_team',
        'regulatory_status': 'approved'
    }
)

# Validate model
validator = ModelValidator(
    model=trained_model,
    test_data=X_test,
    test_labels=y_test,
    model_type='classifier'
)

validation_results = validator.validate_full()
print(f"Model valid: {validation_results['is_valid']}")
print(f"Validation report:\n{validation_results['report']}")
```

#### 2. Monitor for drift

```python
from src.core.drift_detector import DriftDetector

detector = DriftDetector(
    reference_data=X_train,
    reference_predictions=y_train_pred,
    model=credit_model,
    thresholds={'data_drift': 0.05, 'prediction_drift': 0.1}
)

# Daily monitoring
monitoring_results = detector.detect_drift(
    new_data=X_production,
    new_predictions=y_prod_pred
)

if monitoring_results['data_drift_detected']:
    print("⚠️ Data drift detected!")
    print(f"Affected features: {monitoring_results['affected_features']}")
```

#### 3. Generate SHAP explanations

```python
from src.core.explainer import ModelExplainer
import shap

explainer_engine = ModelExplainer(model=credit_model)

# Generate SHAP values
shap_values = explainer_engine.explain_instance(
    instance=X_test.iloc[0],
    method='shap',
    background_samples=X_train[:100]
)

# Generate audit-trail report
audit_report = explainer_engine.generate_audit_report(
    prediction=y_pred[0],
    shap_values=shap_values,
    feature_names=X_test.columns,
    threshold=0.7
)

print(audit_report)
```

#### 4. Compliance logging

```python
from src.compliance.bcbs239_logger import BCBS239Logger
from src.compliance.audit_trail import AuditTrail

# Initialize compliance logger
compliance = BCBS239Logger(
    institution_id='BANK001',
    model_id='credit_scoring_v2.1'
)

audit = AuditTrail(storage='postgresql', connection_string=DB_URI)

# Log validation event
compliance.log_validation(
    timestamp=datetime.now(),
    model_id='credit_scoring_v2.1',
    validation_status='PASSED',
    metrics={
        'accuracy': 0.92,
        'roc_auc': 0.88,
        'gini': 0.76
    },
    validator='risk_team',
    evidence_uri='s3://models/credit_v2.1/validation_report.pdf'
)

# Create audit trail entry
audit.create_entry(
    action='MODEL_VALIDATION',
    model_id='credit_scoring_v2.1',
    actor='risk_analyst_001',
    details=compliance.last_log,
    status='SUCCESS'
)
```

## Core Modules

### `ModelRegistry`
Centralized model governance and versioning
```python
registry.register(name, model, metadata)      # Register new model version
registry.get_production_model(name)            # Fetch current production model
registry.get_model_version(name, version)      # Access specific version
registry.list_models(filters={'domain': 'credit'})  # Query models
```

### `ModelValidator`
Comprehensive model validation framework
```python
validator.validate_schema()                    # Check input/output types
validator.validate_performance()               # Compare metrics vs baselines
validator.validate_fairness()                  # Bias/fairness analysis
validator.validate_stability()                 # Performance consistency
validator.validate_full()                      # All validations
```

### `DriftDetector`
Statistical drift monitoring
```python
detector.detect_data_drift(method='kolmogorov_smirnov')
detector.detect_prediction_drift(method='wasserstein')
detector.detect_performance_drift(metric='roc_auc')
detector.get_drift_report()
```

### `ModelExplainer`
SHAP/LIME-based interpretability
```python
explainer.explain_instance(instance, method='shap')
explainer.feature_importance(method='permutation')
explainer.generate_audit_report(prediction, shap_values)
explainer.plot_explanations()
```

### `BCBS239Logger`
Regulatory compliance and audit logging
```python
logger.log_validation(timestamp, model_id, validation_status, metrics)
logger.log_performance_monitoring(model_id, metrics, timestamp)
logger.log_model_changes(model_id, change_description, approval_id)
logger.generate_compliance_report(period_start, period_end)
```

## Validation Rules & Tests

### Schema Validation
- Input features match expected types and ranges
- Output predictions in valid range [0, 1] for classifiers
- No NaN/Inf values in predictions

### Performance Validation
- Accuracy ≥ baseline (default: 0.85 for credit)
- ROC-AUC ≥ threshold (default: 0.75)
- Gini coefficient stability (max 5% change month-over-month)
- Precision/Recall balance within tolerance

### Fairness Validation
- Disparate impact ratio ≤ 1.25 (80% rule)
- Equalized odds difference ≤ 0.05
- Calibration by protected attributes

### Stability Validation
- Feature distributions stable (KS-test p-value > 0.05)
- Model coefficients within confidence bands
- Prediction volatility < threshold

## Compliance & Regulatory

### BCBS 239 Requirements
- **Governance**: Documented model lineage, approval workflows
- **Validation**: Independent model review and testing
- **Monitoring**: Real-time performance and drift tracking
- **Documentation**: Complete audit trails and decision records

### IFRS 9 Credit Risk
- **Probability of Default (PD)**: Model calibration validation
- **Loss Given Default (LGD)**: Stability and backtesting
- **Exposure at Default (EAD)**: Portfolio-level metrics

## Examples

### Example 1: Credit Scoring Validation
```python
# See examples/credit_score_validation.py
python examples/credit_score_validation.py --model-version 2.1 --test-set prod_2025_q4.csv
```

### Example 2: Fraud Detection Monitoring
```python
# See examples/fraud_detection_monitoring.py
python examples/fraud_detection_monitoring.py --frequency daily --alert-threshold 0.05
```

### Example 3: Capacity Model Audit
```python
# See examples/capacity_model_audit.py
python examples/capacity_model_audit.py --model-id capacity_v3 --audit-depth full
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_validator.py -v

# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# Run compliance tests
pytest tests/test_compliance.py::TestBCBS239Logger -v
```

## CICD Pipeline

### GitHub Actions Workflow (`.github/workflows/ci_cd.yml`)

1. **Code Quality**: Linting, type checking (mypy)
2. **Unit Tests**: pytest with >90% coverage
3. **Model Tests**: Validation framework verification
4. **Integration Tests**: End-to-end compliance workflows
5. **Security**: Dependency scanning (safety, bandit)
6. **Deployment**: MLflow model registry push

```yaml
# Triggered on: push to main, pull requests
# Jobs: lint → test → model_tests → deploy
```

## Performance Characteristics

| Operation | Typical Runtime |
|-----------|-----------------|
| Model validation | 5-30s (depends on data size) |
| SHAP explanations | 2-10s per instance |
| Drift detection | 10-20s for 100K predictions |
| Compliance report generation | 30-60s |

## Troubleshooting

**Issue**: MLflow connection error
```bash
mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./artifacts
```

**Issue**: SHAP memory error on large datasets
```python
# Use sampling
explainer = ModelExplainer(model, sample_size=1000)
```

**Issue**: Drift false positives
```python
# Calibrate thresholds
detector.calibrate_thresholds(historical_data=X_last_year)
```

## Future Enhancements

- [ ] Real-time model serving integration (KServe)
- [ ] AutoML model challenger framework
- [ ] Ensemble explainability (XGBoost + Neural Net)
- [ ] Causal inference for root cause analysis
- [ ] Multi-language support (R, Julia)
- [ ] Kubernetes deployment templates

## Contributing

Contributions welcome! Please:
1. Fork repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Add tests (>90% coverage)
4. Submit pull request with compliance checklist

## Author

**Lucas Barbosa de Oliveira**
- [GitHub](https://github.com/lucas020695)
- [LinkedIn](https://linkedin.com/in/lucas-barbosa-053172353)

## License

MIT License - See LICENSE file for details

---

## Citation

```bibtex
@software{model_audit_toolkit,
  author = {Barbosa de Oliveira, Lucas},
  title = {model-audit-toolkit: Model Risk Management & Compliance Automation},
  year = {2025},
  url = {https://github.com/lucas020695/model-audit-toolkit}
}
```

## References

- [BCBS 239 Principles](https://www.bis.org/publ/bcbs239.pdf)
- [SHAP: A Unified Approach to Interpreting Model Predictions](https://arxiv.org/abs/1705.07874)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Great Expectations Data Quality](https://greatexpectations.io/)
