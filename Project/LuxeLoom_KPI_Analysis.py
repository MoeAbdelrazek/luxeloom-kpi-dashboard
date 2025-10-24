# LuxeLoom KPI Analysis — Script version\n\n# ---\n# \n# # LuxeLoom — E‑commerce KPI Analysis (Agency Level)\n# \n# **Scope:** End-to-end KPI computation for an e-commerce brand, using realistic synthetic data (Shopify-like orders, GA-like sessions, and paid ads).  \n# **Outputs:** Clean daily KPI table, channel rollups, and executive charts.\n# \n# **Stack:** Python (pandas, numpy, matplotlib). No seaborn used. One chart per figure; default colors.\n\n
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = '/mnt/data'
DATASETS = os.path.join(BASE, 'datasets')
ANALYSIS = os.path.join(BASE, 'analysis')
CHARTS = os.path.join(ANALYSIS, 'charts')
os.makedirs(ANALYSIS, exist_ok=True)
os.makedirs(CHARTS, exist_ok=True)

print('Datasets folder:', DATASETS)
print('Analysis folder:', ANALYSIS)
\n\n# ---\n# ## Load datasets\n\n
orders = pd.read_csv(os.path.join(DATASETS, 'orders.csv'), parse_dates=['order_date'])
ads = pd.read_csv(os.path.join(DATASETS, 'ads.csv'), parse_dates=['date'])
sessions = pd.read_csv(os.path.join(DATASETS, 'sessions.csv'), parse_dates=['date'])
customers = pd.read_csv(os.path.join(DATASETS, 'customers.csv'), parse_dates=['signup_date','first_order_date','last_order_date'])
products = pd.read_csv(os.path.join(DATASETS, 'products.csv'))

orders.head(), ads.head(), sessions.head()
\n\n# ---\n# ## Helper functions\n\n
def compute_daily_kpis(orders_df, ads_df, sessions_df):
    # Sales layer
    daily = orders_df.groupby('order_date').agg(
        orders=('order_id','count'),
        revenue=('order_value','sum'),
        cogs=('cogs','sum')
    ).reset_index()
    daily['gross_margin'] = daily['revenue'] - daily['cogs']

    # Ads layer
    ads_daily = ads_df.groupby('date').agg(
        impressions=('impressions','sum'),
        clicks=('clicks','sum'),
        spend=('spend','sum'),
        conversions=('conversions','sum'),
        rev_attr=('revenue_attributed','sum')
    ).reset_index().rename(columns={'date':'order_date'})

    # Sessions layer
    sess_daily = sessions_df.groupby('date').agg(
        sessions=('sessions','sum'),
        bounces=('bounces','sum')
    ).reset_index().rename(columns={'date':'order_date'})
    sess_daily['bounce_rate'] = np.where(sess_daily['sessions']>0, sess_daily['bounces']/sess_daily['sessions'], 0.0)

    # Merge
    kpis = daily.merge(ads_daily, on='order_date', how='left').merge(sess_daily, on='order_date', how='left')
    for col in ['impressions','clicks','spend','conversions','rev_attr','sessions','bounces','bounce_rate']:
        kpis[col] = kpis[col].fillna(0)

    # Final KPIs
    kpis['aov']  = np.where(kpis['orders']>0, kpis['revenue']/kpis['orders'], 0.0)
    kpis['cvr']  = np.where(kpis['sessions']>0, kpis['orders']/kpis['sessions'], 0.0)
    kpis['roas'] = np.where(kpis['spend']>0, kpis['revenue']/kpis['spend'], np.nan)
    kpis['cac']  = np.where(kpis['orders']>0, kpis['spend']/kpis['orders'], np.nan)
    return kpis

def compute_channel_summary(orders_df, ads_df):
    ch_rev = orders_df.groupby('channel').agg(
        revenue=('order_value','sum'),
        orders=('order_id','count')
    ).reset_index()
    ch_ads = ads_df.groupby('channel').agg(
        spend=('spend','sum'),
        clicks=('clicks','sum'),
        impressions=('impressions','sum'),
        conversions=('conversions','sum')
    ).reset_index()
    out = ch_rev.merge(ch_ads, on='channel', how='outer').fillna(0)
    out['aov']  = np.where(out['orders']>0, out['revenue']/out['orders'], 0.0)
    out['roas'] = np.where(out['spend']>0, out['revenue']/out['spend'], np.nan)
    out['ctr']  = np.where(out['impressions']>0, out['clicks']/out['impressions'], 0.0)
    return out
\n\n# ---\n# ## Compute KPI layers\n\n
daily_kpis = compute_daily_kpis(orders, ads, sessions)
channel_kpis = compute_channel_summary(orders, ads)

daily_kpis_path = os.path.join(ANALYSIS, 'daily_kpis.csv')
channel_kpis_path = os.path.join(ANALYSIS, 'kpi_summary_by_channel.csv')
daily_kpis.to_csv(daily_kpis_path, index=False)
channel_kpis.to_csv(channel_kpis_path, index=False)

daily_kpis.tail(3), channel_kpis
\n\n# ---\n# ## Executive charts (matplotlib, default colors)\n\n
plt.figure(figsize=(10,5))
plt.plot(daily_kpis['order_date'], daily_kpis['revenue'])
plt.title('Daily Revenue Trend')
plt.xlabel('Date'); plt.ylabel('Revenue')
plt.tight_layout()
rev_path = os.path.join(CHARTS, 'revenue_trend.png')
plt.savefig(rev_path); plt.close()
rev_path
\n\n
plt.figure(figsize=(10,5))
plt.plot(daily_kpis['order_date'], daily_kpis['roas'])
plt.title('Daily ROAS Trend')
plt.xlabel('Date'); plt.ylabel('ROAS')
plt.tight_layout()
roas_path = os.path.join(CHARTS, 'roas_trend.png')
plt.savefig(roas_path); plt.close()
roas_path
\n\n
plt.figure(figsize=(10,5))
plt.plot(daily_kpis['order_date'], daily_kpis['cac'])
plt.title('Daily CAC Trend')
plt.xlabel('Date'); plt.ylabel('CAC')
plt.tight_layout()
cac_path = os.path.join(CHARTS, 'cac_trend.png')
plt.savefig(cac_path); plt.close()
cac_path
\n\n
valid = channel_kpis.dropna(subset=['roas'])
plt.figure(figsize=(8,5))
plt.bar(valid['channel'], valid['roas'])
plt.title('ROAS by Channel (6 months)')
plt.xlabel('Channel'); plt.ylabel('ROAS')
plt.tight_layout()
bar_path = os.path.join(CHARTS, 'channel_roas_bar.png')
plt.savefig(bar_path); plt.close()
bar_path
\n\n# ---\n# \n# ## Insights scaffolding (fill with numbers from the tables)\n# - **Top channel by ROAS:** Identify highest `roas` in `channel_kpis`.\n# - **Efficiency lever:** Compare CAC trend; note weekends vs weekdays.\n# - **Email efficiency:** Low spend, steady conversions — validates lifecycle campaigns.\n# - **Device behavior:** (Optional) Join sessions by device for CVR differences.\n# - **Budget move:** Shift budget from lowest quartile ROAS campaigns to top quartile.\n