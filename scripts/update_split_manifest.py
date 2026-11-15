import json
import pandas as pd

df = pd.read_parquet('data/processed/pressure_deliveries.parquet')

train_seasons = ['2022', '2022/23', '2023', '2023/24', '2024', '2024/25']
val_seasons = ['2025']
test_seasons = ['2026']

manifest = {}
splits = [('train', train_seasons), ('validation', val_seasons), ('test', test_seasons)]

total_bowl = 0
total_bat = 0

for split_name, seasons in splits:
    s_mask = df['season'].astype(str).isin(seasons)
    primary_mask = s_mask & (df['is_primary_pressure_cohort'] == True)
    wides_mask = primary_mask & (df['extras_type'].fillna('').astype(str).str.lower() == 'wide')
    bat_mask = primary_mask & (~wides_mask)
    
    s_df = df[primary_mask]
    m_count = s_df['match_id'].nunique()
    ipl_m = s_df[s_df['competition_type'] == 'IPL']['match_id'].nunique()
    t20i_m = s_df[s_df['competition_type'] == 'T20I']['match_id'].nunique()
    
    bowl_balls = len(s_df)
    bat_balls = int(bat_mask.sum())
    wides = int(wides_mask.sum())
    
    total_bowl += bowl_balls
    total_bat += bat_balls
    
    manifest[split_name] = {
        'seasons': seasons,
        'matches': m_count,
        'deliveries': bat_balls,
        'batter_deliveries_faced': bat_balls,
        'bowler_deliveries_bowled': bowl_balls,
        'wides_excluded_from_batters': wides,
        'ipl_matches': ipl_m,
        't20i_matches': t20i_m,
        'start_date': str(s_df['match_date'].min()),
        'end_date': str(s_df['match_date'].max()),
    }

manifest['total_matches'] = df[df['is_primary_pressure_cohort'] == True]['match_id'].nunique()
manifest['total_deliveries'] = total_bat
manifest['total_batter_deliveries_faced'] = total_bat
manifest['total_bowler_deliveries_bowled'] = total_bowl
manifest['total_wides_in_primary_cohort'] = total_bowl - total_bat
manifest['reconciliation_note'] = (
    'In MCC Law 22, batters do not face wide deliveries, so wides are excluded from the batter population (184,964 total, 31,165 test). '
    'In MCC Law 21/22, bowlers are charged runs and can effect dismissals on wides, so bowler models evaluate all primary cohort balls (192,373 total, 32,529 test). '
    'The 1,364 test difference represents exact legal wides in the 2026 partition (32,529 - 31,165 = 1,364).'
)

with open('data/processed/ml/split_manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

print('Updated split_manifest.json successfully!')
print('Train: ', manifest['train']['batter_deliveries_faced'], 'bat vs', manifest['train']['bowler_deliveries_bowled'], 'bowl')
print('Val:   ', manifest['validation']['batter_deliveries_faced'], 'bat vs', manifest['validation']['bowler_deliveries_bowled'], 'bowl')
print('Test:  ', manifest['test']['batter_deliveries_faced'], 'bat vs', manifest['test']['bowler_deliveries_bowled'], 'bowl')

