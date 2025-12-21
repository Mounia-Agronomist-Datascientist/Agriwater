"""
Visualization module for irrigation data analysis.

This module provides functions to create various charts:
- Weather data visualization (ET0, precipitation, temperature)
- ETc comparison charts
- Water balance visualization
- Irrigation needs summary

Author: Mounia Tonazzini
Date: December 2025
"""

import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Set style for all plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class IrrigationVisualizer:
    """
    Class for creating visualizations of irrigation data.
    
    Attributes:
        - weather_data (pd.DataFrame): Weather data with ET0, precipitation, etc.
        - crop_name (str): Name of the crop
        - crop_kc (float): Crop coefficient
    """
    
    def __init__(self, weather_data: pd.DataFrame, crop_name: str = "Crop", crop_kc: float = 1.0):
   
        self.weather_data = weather_data.copy()
        self.crop_name = crop_name
        self.crop_kc = crop_kc
        
        # Ensure date column is datetime
        if 'date' in self.weather_data.columns:
            self.weather_data['date'] = pd.to_datetime(self.weather_data['date'])
        
        # Calculate ETc if not already present
        if 'etc' not in self.weather_data.columns and 'et0_fao' in self.weather_data.columns:
            self.weather_data['etc'] = self.weather_data['et0_fao'] * self.crop_kc
    
    
    def plot_weather_overview(self, save_path: str|None = None) -> None:
        """
        Creates a comprehensive weather overview plot with ET0 and precipitation.
        
        Args:save_path (str, optional): Path to save the figure. If None, displays the plot.
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Plot 1: ET0 and Temperature
        color_et0 = 'tab:orange'
        ax1.set_ylabel('ET0 (mm/day)', color=color_et0, fontweight='bold')
        line1 = ax1.plot(self.weather_data['date'], self.weather_data['et0_fao'], 
                        color=color_et0, marker='o', linewidth=2, label='ET0')
        ax1.tick_params(axis='y', labelcolor=color_et0)
        ax1.grid(True, alpha=0.3)
        
        # Add temperature on secondary axis
        ax1_temp = ax1.twinx()
        color_temp = 'tab:red'
        ax1_temp.set_ylabel('Temperature (°C)', color=color_temp, fontweight='bold')
        line2 = ax1_temp.plot(self.weather_data['date'], self.weather_data['temp_mean'], 
                             color=color_temp, linestyle='--', alpha=0.6, label='Temperature')
        ax1_temp.tick_params(axis='y', labelcolor=color_temp)
        
        # Combined legend
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left')
        
        ax1.set_title(f'Weather Overview - {self.crop_name}', fontsize=14, fontweight='bold')
        
        # Plot 2: Precipitation
        color_precip = 'tab:blue'
        ax2.bar(self.weather_data['date'], self.weather_data['precipitation'], 
                color=color_precip, alpha=0.7, label='Precipitation')
        ax2.set_ylabel('Precipitation (mm)', color=color_precip, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor=color_precip)
        ax2.set_xlabel('Date', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper left')
        
        # Format x-axis
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Weather overview plot saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    
    def plot_etc_comparison(self, save_path:  str|None = None) -> None:
        """
        Creates a comparison plot between ET0 and ETc.
        
        Args:save_path (str, optional): Path to save the figure. If None, displays the plot.
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot ET0 and ETc
        ax.plot(self.weather_data['date'], self.weather_data['et0_fao'], 
                marker='s', linewidth=2, label='ET0 (Reference)', color='tab:gray')
        ax.plot(self.weather_data['date'], self.weather_data['etc'], 
                marker='o', linewidth=2.5, label=f'ETc ({self.crop_name})', color='tab:green')
        
        # Fill area between curves
        ax.fill_between(self.weather_data['date'], 
                       self.weather_data['et0_fao'], 
                       self.weather_data['etc'], 
                       alpha=0.2, color='tab:green')
        
        ax.set_xlabel('Date', fontweight='bold')
        ax.set_ylabel('Evapotranspiration (mm/day)', fontweight='bold')
        ax.set_title(f'Crop Evapotranspiration (ETc) vs Reference (ET0) - Kc = {self.crop_kc:.2f}', 
                    fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Add average lines
        avg_et0 = self.weather_data['et0_fao'].mean()
        avg_etc = self.weather_data['etc'].mean()
        ax.axhline(y=avg_et0, color='gray', linestyle='--', alpha=0.5, 
                  label=f'Avg ET0: {avg_et0:.2f} mm/day')
        ax.axhline(y=avg_etc, color='green', linestyle='--', alpha=0.5, 
                  label=f'Avg ETc: {avg_etc:.2f} mm/day')
        ax.legend(loc='upper left', fontsize=10)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"ETc comparison plot saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    
    def plot_water_balance(self, period_days: int = 7, save_path:  str|None = None) -> None:
        """
        Creates a water balance visualization showing ETc, precipitation, and net irrigation need.
        
        Args:
            period_days (int): Number of days to consider for the balance
            save_path (str, optional): Path to save the figure. If None, displays the plot.
        """
        # Calculate totals
        total_etc = self.weather_data['etc'].tail(period_days).sum()
        total_precip = self.weather_data['precipitation'].tail(period_days).sum()
        net_irrigation = max(0, total_etc - total_precip)
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Plot 1: Daily water balance (stacked bars)
        data_period = self.weather_data.tail(period_days).copy()
        
        x_pos = range(len(data_period))
        ax1.bar(x_pos, data_period['etc'], label='ETc (Crop water need)', 
               color='tab:orange', alpha=0.8)
        ax1.bar(x_pos, data_period['precipitation'], label='Precipitation', 
               color='tab:blue', alpha=0.8)
        
        ax1.set_xlabel('Days', fontweight='bold')
        ax1.set_ylabel('Water (mm/day)', fontweight='bold')
        ax1.set_title(f'Daily Water Balance - Last {period_days} Days', 
                     fontsize=13, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Plot 2: Cumulative water balance (pie chart)
        values = [total_etc, total_precip, net_irrigation]
        labels = [f'Total ETc\n{total_etc:.1f} mm', 
                 f'Total Precipitation\n{total_precip:.1f} mm',
                 f'Net Irrigation Need\n{net_irrigation:.1f} mm']
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        
        # Only show non-zero values
        non_zero_values = [(v, l, c) for v, l, c in zip(values, labels, colors) if v > 0]
        if non_zero_values:
            values_nz, labels_nz, colors_nz = zip(*non_zero_values)
            
            wedges, texts, autotexts = ax2.pie(values_nz, labels=labels_nz, colors=colors_nz,
                                                autopct='%1.1f%%', startangle=90,
                                                textprops={'fontsize': 10, 'weight': 'bold'})
            
            ax2.set_title(f'Water Balance Summary ({period_days} days)', 
                         fontsize=13, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Water balance plot saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    
    def plot_irrigation_recommendation(self, surface_ha: float, 
                                      irrigation_results: dict,
                                      save_path:  str|None = None) -> None:
        """
        Creates a visual summary of irrigation recommendations.
        
        Args:
            - surface_ha (float): Surface area in hectares
            - irrigation_results (dict): Results from irrigation calculator
            - save_path (str, optional): Path to save the figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Data for bar chart
        categories = ['Total Water\nNeed (ETc)', 'Effective\nPrecipitation', 
                     'Net Irrigation\nNeed', 'Gross Irrigation\n(with losses)']
        values = [
            irrigation_results['total_etc_mm'],
            irrigation_results['total_precipitation_mm'],
            irrigation_results['net_irrigation_need_mm'],
            irrigation_results['gross_irrigation_need_mm']
        ]
        colors = ['#ff6b6b', '#4ecdc4', '#ffd93d', '#ff8c42']
        
        bars = ax.bar(categories, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f} mm',
                   ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        ax.set_ylabel('Water Depth (mm)', fontweight='bold', fontsize=12)
        ax.set_title(f'Irrigation Recommendation - {self.crop_name} ({surface_ha:.1f} ha)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add volume in m³ as text
        volume_text = f"Total irrigation volume needed: {irrigation_results['gross_volume_m3']:.0f} m³"
        ax.text(0.5, 0.95, volume_text, transform=ax.transAxes,
               ha='center', va='top', fontsize=12, fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Irrigation recommendation plot saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    
    def create_all_plots(self, surface_ha: float, irrigation_results: dict,
                        output_dir: str = "output") -> None:
        """
        Creates all visualization plots and save them to a directory.
        
        Args:
            - surface_ha (float): Surface area in hectares
            - irrigation_results (dict): Results from irrigation calculator
            - output_dir (str): Directory to save plots (default: 'output')
        """
        import os
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Creating all visualization plots...")
        print(f"Output directory: {output_dir}/\n")
        
        # Generate all plots
        self.plot_weather_overview(save_path=f"{output_dir}/weather_overview.png")
        self.plot_etc_comparison(save_path=f"{output_dir}/etc_comparison.png")
        self.plot_water_balance(
            period_days=len(self.weather_data),
            save_path=f"{output_dir}/water_balance.png"
        )
        self.plot_irrigation_recommendation(
            surface_ha=surface_ha,
            irrigation_results=irrigation_results,
            save_path=f"{output_dir}/irrigation_recommendation.png"
        )
        
        print(f"\nAll plots created successfully in '{output_dir}/' directory")


# __________ Example usage for testing __________ 

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from src.meteo_api import MeteoAPI
    from src.evapotranspiration import EvapotranspirationCalculator
    
    print("="*70)
    print("TESTING VISUALIZATION MODULE")
    print("="*70)
    
    # Fetch real weather data
    print("\nFetching weather data for Montpellier...")
    meteo = MeteoAPI(latitude=43.6109, longitude=3.8772)
    weather_data = meteo.fetch_weather_data(days_count=7)
    
    if weather_data is not None:
        # Create evapotranspiration calculator for corn
        crop_kc = 1.2
        crop_name = "Corn (Mid-season)"
        
        et_calc = EvapotranspirationCalculator(
            weather_data=weather_data,
            crop_kc=crop_kc,
            crop_name=crop_name
        )
        
        # Calculate irrigation results
        irrigation_results = et_calc.calculate_irrigation_volume(
            surface_ha=10.0,
            period_days=7,
            efficiency=0.85
        )
        
        # Create visualizer
        viz = IrrigationVisualizer(
            weather_data=weather_data,
            crop_name=crop_name,
            crop_kc=crop_kc
        )
        
        # Create all plots
        viz.create_all_plots(
            surface_ha=10.0,
            irrigation_results=irrigation_results,
            output_dir="output"
        )
        
        print("\n" + "="*70)
        print("Testing completed successfully!")
        print("Check the 'output/' directory for generated plots.")
        print("="*70)
    
    else:
        print("Failed to fetch weather data. Cannot create visualizations.")