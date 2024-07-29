
import pandas as pd
import numpy as np
from IPython.display import display, HTML
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from adjustText import adjust_text

def update_tables(df, year, internet_type, region):
    try:
        plt.rcParams['font.family'] = 'Arial'
        plt.rcParams['font.size'] = 14

        palette = ListedColormap(["#a1d99b", "#74c476", "#31a354", "#006d2c", "#00441b"])

        internet_type_map = {
            'Mobile Internet': 'mobile',
            'Fixed Internet': 'fixed'
        }
        internal_internet_type = internet_type_map[internet_type]  # Map display value to internal value

        df2 = df.drop(columns=['geometry'])

        df_year = df2[(df2['year'] == year) & 
                     (df2['d_type'] == internal_internet_type) & 
                     (df2['k_tests'] >= 1) &
                     ((df2['REGION_WB'] == region) | (region == 'World'))].drop_duplicates(subset=['Country']).copy()

        df_last = df2[(df2['year'] == year-1) & 
                     (df2['d_type'] == internal_internet_type)  & 
                     (df2['k_tests'] >= 1) &
                     ((df2['REGION_WB'] == region) | (region == 'World'))].drop_duplicates(subset=['Country']).copy()

        # Rank countries based on avg_d_mbps and avg_d_mbps_w for the selected year and previous year
        df_year['rank_avg_d_mbps'] = df_year['avg_d_mbps'].rank(ascending=False)
        df_year['rank_avg_d_mbps_w'] = df_year['avg_d_mbps_w'].rank(ascending=False)

        df_last['rank_avg_d_mbps'] = df_last['avg_d_mbps'].rank(ascending=False)
        df_last['rank_avg_d_mbps_w'] = df_last['avg_d_mbps_w'].rank(ascending=False)

        # Merge data for selected year and previous year to calculate rank changes
        df_merged = pd.merge(df_year[['Country', 'avg_d_mbps', 'avg_d_mbps_w', 'rank_avg_d_mbps', 'rank_avg_d_mbps_w']],
                             df_last[['Country', 'rank_avg_d_mbps', 'rank_avg_d_mbps_w']],
                             on='Country', how='left',
                             suffixes=('', '_last'))

        df_merged['rank_change_avg_d_mbps'] = (df_merged['rank_avg_d_mbps_last'] - df_merged['rank_avg_d_mbps']).fillna(0).astype(int)
        df_merged['rank_change_avg_d_mbps_w'] = (df_merged['rank_avg_d_mbps_w_last'] - df_merged['rank_avg_d_mbps_w']).fillna(0).astype(int)

        def format_rank_change(change):
            if change > 0:
                arrow = '▲'
                color = 'green'
            elif change < 0:
                arrow = '▼'
                color = 'red'
            else:
                arrow = '➖'  # Icon for no change
                color = 'grey'
            return f'<span style="color: {color};">{arrow} {abs(change) if change != 0 else ""}</span>'

        df_merged['rank_change_avg_d_mbps'] = df_merged.apply(
            lambda x: format_rank_change(x['rank_change_avg_d_mbps']), axis=1)

        df_merged['rank_change_avg_d_mbps_w'] = df_merged.apply(
            lambda x: format_rank_change(x['rank_change_avg_d_mbps_w']), axis=1)

        df_sorted_speed = df_merged[['Country', 'avg_d_mbps', 'rank_avg_d_mbps', 'rank_change_avg_d_mbps']].sort_values(by='avg_d_mbps', ascending=False)
        df_sorted_speed_w = df_merged[['Country', 'avg_d_mbps_w', 'rank_avg_d_mbps_w', 'rank_change_avg_d_mbps_w']].sort_values(by='avg_d_mbps_w', ascending=False)

        df_sorted_speed['Color'] = get_color_palette(df_sorted_speed['avg_d_mbps'], palette)
        df_sorted_speed = df_sorted_speed.rename(columns={'avg_d_mbps': 'Mbps', 'rank_avg_d_mbps': '#', 'rank_change_avg_d_mbps': 'Rank Change'})

        df_sorted_speed_w['Color'] = get_color_palette(df_sorted_speed_w['avg_d_mbps_w'], palette)
        df_sorted_speed_w = df_sorted_speed_w.rename(columns={'avg_d_mbps_w': 'Mbps', 'rank_avg_d_mbps_w': '#', 'rank_change_avg_d_mbps_w': 'Rank Change'})

        max_speed = df_sorted_speed['Mbps'].max()
        max_speed_w = df_sorted_speed_w['Mbps'].max()

        html_speed = df_sorted_speed.to_html(index=False, columns=['#', 'Country', 'Mbps', 'Rank Change'],
                                             header=[f'<b style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">{year} - {internet_type} Download Speed <i class="fa fa-download"></i></b>', 'Country', f'<b style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">Download Speed (Mbps)</b>', 'Rank Change'],
                                             formatters={'#': '{:,.0f}'.format,
                                                         'Country': lambda x: f'<div style="text-align: left; font-family: Arial; font-weight: bold;">{x}</div>',
                                                         'Mbps': lambda x: f'<span style="color: {df_sorted_speed.loc[df_sorted_speed["Mbps"] == x, "Color"].values[0]}; font-weight: bold; font-size: 16px; font-family: Arial;">{x:.1f}</span><br>{create_bar(x, max_speed)}',
                                                         'Rank Change': str},
                                             escape=False,
                                             table_id='speed_table')

        html_speed_w = df_sorted_speed_w.to_html(index=False, columns=['#', 'Country', 'Mbps', 'Rank Change'],
                                                 header=[f'<b style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">{year} - {internet_type} Download Speed Weighted <i class="fa fa-download"></i></b>', 'Country', f'<b style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">Download Speed Weighted by Population (Mbps)</b>', 'Rank Change'],
                                                 formatters={'#': '{:,.0f}'.format,
                                                             'Country': lambda x: f'<div style="text-align: left; font-family: Arial; font-weight: bold;">{x}</div>',
                                                             'Mbps': lambda x: f'<span style="color: {df_sorted_speed_w.loc[df_sorted_speed_w["Mbps"] == x, "Color"].values[0]}; font-weight: bold; font-size: 16px; font-family: Arial;">{x:.1f}</span><br>{create_bar(x, max_speed_w)}',
                                                             'Rank Change': str},
                                                 escape=False,
                                                 table_id='speed_table')

        html_speed = f'''
            <style>
                #speed_table th:nth-child(3) {{ width: 150px; }}
                #speed_table td:nth-child(3) {{ width: 150px; }}
            </style>
            {html_speed}
        '''

        html_speed_w = f'''
            <style>
                #speed_table th:nth-child(3) {{ width: 150px; }}
                #speed_table td:nth-child(3) {{ width: 150px; }}
            </style>
            {html_speed_w}
        '''

        display(HTML(f'''
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <h3 style="font-family: Arial; font-weight: bold; font-size: 16px; color: black;">{year} - {internet_type} Download Speed in {region}</h3>
                <div style="display: flex; justify-content: space-between;">
                    <div style="flex: 1; padding-right: 10px;">
                        <h4 style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">Simple Average</h4>
                        {html_speed}
                    </div>
                    <div style="flex: 1; padding-left: 10px;">
                        <h4 style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">Average Weighted by Population</h4>
                        {html_speed_w}
                    </div>
                </div>
            </div>
        '''))

        display(HTML('''
        <style>
            .widget-dropdown select {
                font-family: Arial, sans-serif !important;
                font-size: 14px !important;
                color: black !important;
            }
            .widget-dropdown {
                font-family: Arial, sans-serif !important;
            }
            .widget-dropdown label {
                font-family: Arial, sans-serif !important;
                font-size: 14px !important;
                color: black !important;
            }
            .widget-dropdown .widget-title {
                font-family: Arial, sans-serif !important;
                font-size: 14px !important;
                color: black !important;
            }
        </style>
        '''))

         # Update maps
        update_map(df, year, internal_internet_type, region)

    except Exception as e:
        print(f"Error updating tables: {e}")



def get_color_palette(speed_series, palette):
    normed = (speed_series - speed_series.min()) / (speed_series.max() - speed_series.min())
    colors = plt.get_cmap(palette)(normed)
    n_count = min(len(speed_series)-1, 10)
    colors[n_count:] = colors[n_count]
    return [f'rgb{tuple(int(c * 255) for c in color[:3])}' for color in colors]

def create_bar(value, max_value):
    percentage = value / max_value * 100
    return f'<div style="background-color: #a1d99b; width: {percentage}%; height: 8px; margin-top: 2px;"></div>'


def plot_geodata(ax, gdf, variable, title, labels, num_bins=7, bin_cutoffs=None, palette=None, leg_pos=1, dec_pos_legend=0):
    
    if bin_cutoffs is None:
        raise ValueError("bin_cutoffs must be provided.")
    else:
        gdf['dl_cat'] = pd.cut(gdf[variable], bins=bin_cutoffs, labels=False, include_lowest=True)
        legend_labels = [f'{bin_cutoffs[i]:.{dec_pos_legend}f} to {bin_cutoffs[i+1]:.{dec_pos_legend}f}' for i in range(len(bin_cutoffs)-1)]

    if palette is None:
        raise ValueError("Palette must be provided.")
    palette_filtered = palette[:len(legend_labels)]  # Adjust to number of bins

    gdf.plot(column='dl_cat', cmap=ListedColormap(palette_filtered), 
             linewidth=0.4, ax=ax, legend=False,
             edgecolor='0.7', missing_kwds={"color": "gray", "label": "No data", 'hatch':'//'})

    no_data_patch = Patch(facecolor='gray', edgecolor='0.7', hatch='//', label='No data')
    handles = [Patch(facecolor=color, edgecolor='black', label=label) for color, label in zip(palette_filtered, legend_labels)]
    handles_f = handles + [no_data_patch]

    if leg_pos == 1:
        ax.legend(handles=handles_f, loc='upper center', bbox_to_anchor=(0.5, 0.05), ncol=len(handles_f), 
                  title=labels, alignment='left', frameon=False, prop={'size': 12},
                  handlelength=3, handletextpad=0.5, title_fontsize='large', labelspacing=0.8, columnspacing=0.45)
    elif leg_pos == 2:
        ax.legend(handles=handles_f, loc='upper right', bbox_to_anchor=(0.2, 0.5), ncol=1, title=labels, 
                  alignment='left', frameon=False)
    else:
        sm = plt.cm.ScalarMappable(cmap=ListedColormap(palette_filtered), norm=BoundaryNorm(bin_cutoffs, len(bin_cutoffs) - 1))
        sm._A = []
        cbar = plt.colorbar(sm, orientation='horizontal', pad=0.05, aspect=50, shrink=0.6, ax=ax)
        cbar.set_label(labels)
        cbar.set_ticks(bin_cutoffs)
        cbar.set_ticklabels([f'{bin_cutoffs[i]:.{dec_pos_legend}f}' for i in range(len(bin_cutoffs))])

        plt.legend(handles=[no_data_patch], loc='center left', bbox_to_anchor=(0.8, 0.0), fancybox=True, shadow=True)

    #ax.set_title(title, fontsize=18, color='#404040', pad=10, loc='left')
    ax.set_axis_off()

def update_map(data, year, internal_internet_type, region):
    plt.rcParams['font.family'] = 'DejaVu Serif'
    plt.rcParams['font.size'] = 12
    
    #title = f'{internet_type} Speed, {year} ({"Weighted by Population" if population == "Weighted" else "Not Weighted"})'
    
    df_filtered = data[(data['year'] == year) & 
                       (data['d_type'] == internal_internet_type) &
                       ((data['REGION_WB'] == region) | (region == 'World'))].copy()

    df_filtered.loc[df_filtered['k_tests'] < 1, 'avg_d_mbps'] = np.nan
    df_filtered.loc[df_filtered['k_tests'] < 1, 'avg_d_mbps_w'] = np.nan
 
    if region == 'World':
        fig, ax = plt.subplots(1, 2, figsize=(14, 8))
    else:
        fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    
    # Plot for population='Not Weighted'
    plot_geodata(
        ax=ax[0],
        gdf=df_filtered,
        variable='avg_d_mbps',
        title='',
        labels='Mbps',
        num_bins=10,
        bin_cutoffs=get_bin_cutoffs(df_filtered, 'avg_d_mbps'),
        palette=["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#31a354", "#006d2c", "#005a29", "#00441b", "#00351d"],
        dec_pos_legend=0,
        leg_pos=3
    )
    
    # Plot for population='Weighted'
    plot_geodata(
        ax=ax[1],
        gdf=df_filtered,
        variable='avg_d_mbps_w',
        title='',
        labels='Mbps',
        num_bins=10,
        bin_cutoffs=get_bin_cutoffs(df_filtered, 'avg_d_mbps_w'),
        palette=["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#31a354", "#006d2c", "#005a29", "#00441b", "#00351d"],
        dec_pos_legend=0,
        leg_pos=3
    )
    
    plt.tight_layout()
    plt.show()


def get_bin_cutoffs(df, variable, num_bins=10):
    valid_data = df[variable].dropna()
    bin_cutoffs = np.percentile(valid_data, np.linspace(0, 100, num_bins + 1))
    bin_cutoffs = np.unique(bin_cutoffs) 
    return bin_cutoffs


def plot_scatter(df, year, internet_type, region):
    plt.rcParams['font.family'] = 'DejaVu Serif'
    plt.rcParams['font.size'] = 12
    
    internet_type_map = {
        'Mobile Internet': 'mobile',
        'Fixed Internet': 'fixed'
    }
    
    internal_internet_type = internet_type_map[internet_type]
    
    df_filtered = df[(df['year'] == year) & 
                     (df['d_type'] == internal_internet_type) & 
                     ((df['REGION_WB'] == region) | (region == 'World')) & 
                     (df['k_tests'] >= 1)].copy()
    df_filtered = df_filtered.drop_duplicates(subset='Country')
    
    x = df_filtered['avg_d_mbps']
    y = df_filtered['avg_d_mbps_w']
    
    # Calculate deviations and percentage differences
    df_filtered['deviation'] = abs(x - y)
    df_filtered['pct_diff'] = ((y - x) / x) * 100
    top_deviations = df_filtered.nlargest(15, 'deviation')
    
    # Scatter plot
    max_value = max(x.max(), y.max())
    plt.figure(figsize=(10, 8))
    plt.scatter(x, y, color='#31a354', alpha=0.7, edgecolor='k', s=100)
    plt.plot([0, max_value], [0, max_value], linestyle='--', color='grey')
    
    # Add labels for highest deviations
    texts = []
    for _, row in top_deviations.iterrows():
        label = f"{row['Country']} ({row['pct_diff']:.0f}%)"
        texts.append(plt.text(row['avg_d_mbps'], row['avg_d_mbps_w'], label, fontsize=8, fontweight='bold', color='darkred'))
    
    adjust_text(texts, arrowprops=dict(arrowstyle='->', color='black'))
    
    plt.xlabel('Average Download Speed (Mbps)')
    plt.ylabel('Average Download Speed Weighted by Population (Mbps)')
    plt.title(f'{internet_type} {year} Download Speed in {region}')
    plt.grid(True)
    plt.show()
    
def plot_histogram(df, year, internet_type, region):
    plt.rcParams['font.family'] = 'DejaVu Serif'
    plt.rcParams['font.size'] = 12
    
    internet_type_map = {
        'Mobile Internet': 'mobile',
        'Fixed Internet': 'fixed'
    }
    
    internal_internet_type = internet_type_map[internet_type]
    
    df_filtered = df[(df['year'] == year) & 
                     (df['d_type'] == internal_internet_type) & 
                     ((df['REGION_WB'] == region) | (region == 'World')) & 
                     (df['k_tests'] >= 1)].copy()
    df_filtered = df_filtered.drop_duplicates(subset='Country')
    
    x = df_filtered['avg_d_mbps']
    y = df_filtered['avg_d_mbps_w']
    
    # Calculate percentage differences
    df_filtered['pct_diff'] = ((y - x) / x) * 100
    
    # Histogram plot
    plt.figure(figsize=(10, 8))
    plt.hist(df_filtered['pct_diff'], bins=20, color='#31a354', edgecolor='black', alpha=0.7)
    
    # Add vertical line at y=0
    plt.axvline(x=0, color='red', linestyle='--', linewidth=1)
    
    plt.xlabel('Percentage Deviation (%)')
    plt.ylabel('Frequency')
    plt.title(f'Histogram of Percentage Deviation in {internet_type} {year} for {region}')
    plt.grid(axis='y')
    plt.show()
