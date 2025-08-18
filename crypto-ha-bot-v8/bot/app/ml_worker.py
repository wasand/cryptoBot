from .database import get_session
from .models import MarketData, MLFeature
import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests
import uuid

def run_ml_cycle():
    batch_id = str(uuid.uuid4())
    s = get_session()
    df = pd.read_sql("SELECT * FROM market_data WHERE batch_id IN (SELECT DISTINCT batch_id FROM fx_rates)", s.bind)
    if not df.empty:
        try:
            granger_results = grangercausalitytests(df[['price', 'volume']], maxlag=4, verbose=False)
            s.add(MLFeature(batch_id=batch_id, feature_name="granger_causality", value=str(granger_results)))
            s.commit()
        except Exception as e:
            print(f"ML error: {e}")
    s.close()

if __name__ == "__main__":
    run_ml_cycle()