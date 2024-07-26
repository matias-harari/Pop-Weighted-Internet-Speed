import pandas as pd
import numpy as np
from IPython.display import display, HTML
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

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
        
        download_speed_col = f'{year}_{internal_internet_type}_avg_d_mbps'
        download_speed_w_col = f'{year}_{internal_internet_type}_avg_d_mbps_w'
        k_tests_col = f'{year}_{internal_internet_type}_k_tests'

        df_filtered = df.copy() if region == 'World' else df[df['REGION_WB'] == region].copy()
        df_filtered = df_filtered.loc[df_filtered[k_tests_col] >= 1]
        df_filtered = df_filtered.drop_duplicates(subset='Country')

        df_sorted_speed = df_filtered[['Country', download_speed_col]].copy()
        df_sorted_speed['#'] = df_sorted_speed[download_speed_col].rank(ascending=False).astype(int)
        df_sorted_speed = df_sorted_speed.sort_values(by=[download_speed_col], ascending=False)

        df_sorted_speed_w = df_filtered[['Country', download_speed_w_col]].copy()
        df_sorted_speed_w['#'] = df_sorted_speed_w[download_speed_w_col].rank(ascending=False).astype(int)
        df_sorted_speed_w = df_sorted_speed_w.sort_values(by=[download_speed_w_col], ascending=False)

        df_sorted_speed['Color'] = get_color_palette(df_sorted_speed[download_speed_col], palette)
        df_sorted_speed = df_sorted_speed.rename(columns={download_speed_col: 'Mbps'})
        download_speed_col = 'Mbps'

        df_sorted_speed_w['Color'] = get_color_palette(df_sorted_speed_w[download_speed_w_col], palette)
        df_sorted_speed_w = df_sorted_speed_w.rename(columns={download_speed_w_col: 'Mbps'})
        download_speed_w_col = 'Mbps'

        max_speed = df_sorted_speed[download_speed_col].max()
        max_speed_w = df_sorted_speed_w[download_speed_w_col].max()

        html_speed = df_sorted_speed.to_html(index=False, columns=['#', 'Country', download_speed_col],
                                             header=[f'<b style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">{year} - {internet_type} Download Speed <i class="fa fa-download"></i></b>', 'Country', f'<b style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">Download Speed (Mbps)</b>'],
                                             formatters={'#': '{:,.0f}'.format,
                                                         'Country': lambda x: f'<div style="text-align: left; font-family: Arial; font-weight: bold;">{x}</div>',
                                                         download_speed_col: lambda x: f'<span style="color: {df_sorted_speed.loc[df_sorted_speed[download_speed_col] == x, "Color"].values[0]}; font-weight: bold; font-size: 16px; font-family: Arial;">{x:.1f}</span><br>{create_bar(x, max_speed)}'},
                                             escape=False,
                                             table_id='speed_table')

        html_speed_w = df_sorted_speed_w.to_html(index=False, columns=['#', 'Country', download_speed_w_col],
                                                 header=[f'<b style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">{year} - {internet_type} Download Speed Weighted <i class="fa fa-download"></i></b>', 'Country', f'<b style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">Download Speed Weighted by Population (Mbps)</b>'],
                                                 formatters={'#': '{:,.0f}'.format,
                                                             'Country': lambda x: f'<div style="text-align: left; font-family: Arial; font-weight: bold;">{x}</div>',
                                                             download_speed_w_col: lambda x: f'<span style="color: {df_sorted_speed_w.loc[df_sorted_speed_w[download_speed_w_col] == x, "Color"].values[0]}; font-weight: bold; font-size: 16px; font-family: Arial;">{x:.1f}</span><br>{create_bar(x, max_speed_w)}'},
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
            <div style="display: flex; justify-content: space-between;">
                <div style="flex: 1; padding-right: 10px;">
                    <h4 style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">{year} - {internet_type} Download Speed</h4>
                    {html_speed}
                </div>
                <div style="flex: 1; padding-left: 10px;">
                    <h4 style="font-family: Arial; font-weight: bold; font-size: 14px; color: black;">{year} - {internet_type} Download Speed Weighted by Population</h4>
                    {html_speed_w}
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
            .widget-label {
                font-family: Arial, sans-serif !important;
                font-size: 14px !important;
                color: black !important;
            }
        </style>
        '''))
        
        # Update maps
        update_map(df, year, internet_type, region)
        


    except:
        print((f"No {internet_type} data for {year} in {region}"))


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

def update_map(data, year, internet_type, region):
    plt.rcParams['font.family'] = 'DejaVu Serif'
    plt.rcParams['font.size'] = 12
    
    internet_type_map = {
        'Mobile Internet': 'mobile',
        'Fixed Internet': 'fixed'
    }
    
    internal_internet_type = internet_type_map[internet_type]
    #title = f'{internet_type} Speed, {year} ({"Weighted by Population" if population == "Weighted" else "Not Weighted"})'
    variable = f'{year}_{internal_internet_type}_avg_d_mbps'
    k_tests_col = f'{year}_{internal_internet_type}_k_tests'
    
    df_filtered = data.copy() if region == 'World' else data[data['REGION_WB'] == region].copy()
    df_filtered.loc[df_filtered[k_tests_col] < 1, variable] = np.nan

    bin_cutoffs = get_bin_cutoffs(df_filtered, variable)
    
    if region == 'World':
        fig, ax = plt.subplots(1, 2, figsize=(14, 8))
    else:
        fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    
    # Plot for population='Not Weighted'
    plot_geodata(
        ax=ax[0],
        gdf=df_filtered,
        variable=f'{year}_{internal_internet_type}_avg_d_mbps',
        title='',
        labels='Mbps',
        num_bins=10,
        bin_cutoffs=bin_cutoffs,
        palette=["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#31a354", "#006d2c", "#005a29", "#00441b", "#00351d"],
        dec_pos_legend=0,
        leg_pos=3
    )
    
    # Plot for population='Weighted'
    plot_geodata(
        ax=ax[1],
        gdf=df_filtered,
        variable=f'{year}_{internal_internet_type}_avg_d_mbps_w',
        title='',
        labels='Mbps',
        num_bins=10,
        bin_cutoffs=bin_cutoffs,
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