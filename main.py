import streamlit as st
from datetime import datetime, timedelta
import logging
import numpy as np
import pandas as pd
from ui import create_ui
from store import get_data_with_dates, filter_prices_duplicates
from formula import fitting, forecasting, determine_MAPE_list
from chart import plot_fitting, plot_fitting_forecast, plot_mape
from export import create_excel_download
from table import display_raw_data_table  

logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
    handlers=[logging.StreamHandler()]
)

class StockFiltering:
    """Handles data filtering operations."""
    @staticmethod
    def filter_data(fitting_data):
        """Filter duplicates from fitting data."""
        if fitting_data is None or fitting_data.empty:
            st.error("No data to filter.")
            return None, None
        
        if isinstance(fitting_data['Close'], pd.DataFrame):
            st.error("Unexpected data structure: 'Close' column is a DataFrame.")
            logging.error(f"fitting_data['Close'] is a DataFrame: {fitting_data['Close'].head()}")
            return None, None
        
        filtered_data = filter_prices_duplicates(fitting_data)
        if filtered_data.empty:
            st.error("No data remains after filtering duplicates.")
            return None, None
        
        fitting_prices = filtered_data['Close'].tolist()
        fitting_dates = filtered_data.index.tolist()
        return fitting_prices, fitting_dates

class StockDataFetcher:
    """Handles data fetching from Yahoo Finance."""
    @staticmethod
    def fetch_data(stock_symbol, start_date, end_date, forecast_end_date):
        """Fetch stock data for fitting and forecasting periods."""
        with st.spinner("Mengambil dan memproses data..."):
            fitting_data, forecast_data = get_data_with_dates(
                stock_symbol, start_date, end_date, forecast_end_date
            )
            
            if fitting_data is None:
                st.error(f"Tidak dapat mengambil data untuk simbol {stock_symbol}. "
                         f"Pastikan menggunakan simbol saham benar, untuk saham Indonesia "
                         f"dapat ditulis dengan format [simbol saham].JK "
                         f"(contoh: BBCA.JK untuk saham Bank Central Asia Tbk.)")
                st.info("Silakan periksa simbol saham di Yahoo Finance atau coba simbol lain.")
                return None, None, None, None
            
            if len(fitting_data) < 4:
                st.error("Data tidak cukup untuk melakukan forecasting. "
                         "Minimal 4 data point diperlukan. Coba perpanjang periode fitting.")
                return None, None, None, None
            
            fitting_prices = fitting_data['Close'].tolist()
            fitting_dates = fitting_data.index.tolist()
            return fitting_data, forecast_data, fitting_prices, fitting_dates

class StockFitting:
    """Handles stock price fitting operations."""
    @staticmethod
    def perform_fitting(fitting_prices, stock_symbol):
        """Perform fitting on stock prices."""
        Fitting_S_n_list, v_list = fitting(fitting_prices, stock_symbol)
        if not Fitting_S_n_list:
            st.error("Gagal melakukan fitting data.")
            return None, None
        mape_fit = determine_MAPE_list(fitting_prices, Fitting_S_n_list)
        return Fitting_S_n_list, v_list, mape_fit

class StockForecasting:
    """Handles stock price forecasting operations."""
    @staticmethod
    def perform_forecasting(Fitting_S_n_list, forecast_data, stock_symbol):
        """Perform forecasting based on fitting results."""
        S_forecast, forecast_dates, actual_forecast_prices = forecasting(
            Fitting_S_n_list, forecast_data, stock_symbol
        )
        mape_forecast = []
        if S_forecast and actual_forecast_prices:
            mape_forecast = determine_MAPE_list(actual_forecast_prices, S_forecast)
        return S_forecast, forecast_dates, actual_forecast_prices, mape_forecast

class StockVisualizer:
    """Handles visualization of fitting and forecasting results."""
    @staticmethod
    def display_results(stock_symbol, fitting_data, forecast_data, start_date, end_date, 
                       forecast_end_date, fitting_prices, fitting_dates, Fitting_S_n_list, 
                       S_forecast, forecast_dates, actual_forecast_prices, mape_fit, mape_forecast):
        """Display all results including tables and charts."""
        st.success("Selesai!")

        # Display raw data table
        display_raw_data_table(stock_symbol, fitting_data, forecast_data, 
                              start_date, end_date, forecast_end_date)

        # Display summary statistics
        if Fitting_S_n_list:
            st.subheader("📊 Statistic Details")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Jumlah Data Fitting", len(fitting_prices))
            with col2:
                if mape_fit:
                    st.metric("MAPE Fitting", f"{np.mean(mape_fit):.2f}%")
            with col3:
                if mape_forecast:
                    st.metric("MAPE Forecast", f"{np.mean(mape_forecast):.2f}%")
            with col4:
                forecast_days_actual = len(S_forecast) if S_forecast else 0
                st.metric("Periode Forecast", f"{forecast_days_actual} hari")

            # Plot charts
            plot_fitting(stock_symbol, fitting_dates, fitting_prices, Fitting_S_n_list)
            
            if S_forecast and actual_forecast_prices:
                plot_fitting_forecast(
                    stock_symbol, 
                    fitting_dates, fitting_prices, Fitting_S_n_list,
                    forecast_dates, S_forecast, actual_forecast_prices
                )
            
            if mape_fit:
                plot_mape(stock_symbol, mape_fit, "Fitting", np.mean(mape_fit))
            
            if mape_forecast:
                plot_mape(stock_symbol, mape_forecast, "Forecast", np.mean(mape_forecast))

class StockExporter:
    """Handles exporting analysis results to Excel."""
    @staticmethod
    def export_to_excel(stock_symbol, fitting_dates, fitting_prices, Fitting_S_n_list, 
                        forecast_dates, S_forecast, actual_forecast_prices, start_date, forecast_end_date):
        """Create and provide Excel download for analysis results."""
        st.subheader("💾 Download Data")
        try:
            excel_data = create_excel_download(
                stock_symbol=stock_symbol,
                fitting_dates=fitting_dates,
                fitting_prices=fitting_prices,
                Fitting_S_n_list=Fitting_S_n_list,
                forecast_dates=forecast_dates if forecast_dates else [],
                S_forecast=S_forecast if S_forecast else [],
                actual_forecast_prices=actual_forecast_prices if actual_forecast_prices else []
            )
            
            filename = f"{stock_symbol}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            st.download_button(
                label="📥 Download Excel Report",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download complete analysis data in Excel format"
            )
            
            st.info(f"📊 File akan berisi data dari {start_date} hingga {forecast_end_date}")
            
        except Exception as e:
            st.error(f"Error creating Excel file: {str(e)}")
            logging.error(f"Excel creation error: {e}")

class StockForecaster:
    def __init__(self):
        """Initialize the StockForecaster with UI inputs."""
        self.stock_symbol, self.start_date, self.training_days, self.forecast_days, \
        self.end_date, self.forecast_end_date = create_ui()
        self.today = datetime.today().date()
        self.max_fitting_date = self.today - timedelta(days=2)

    def validate_inputs(self):
        """Validate user inputs."""
        if self.start_date >= self.end_date:
            st.error("Start date harus lebih kecil dari end date!")
            return False
        elif self.end_date >= self.forecast_end_date:
            st.error("End date harus lebih kecil dari forecast end date!")
            return False
        elif self.end_date > self.max_fitting_date:
            st.error(f"End date ({self.end_date.strftime('%d/%m/%Y')}) tidak boleh melebihi "
                     f"{self.max_fitting_date.strftime('%d/%m/%Y')} "
                     f"(2 hari sebelum hari ini: {self.today.strftime('%d/%m/%Y')})!")
            return False
        return True

    def run(self):
        """Main method to run the forecasting application."""
        run_forecast = st.button("🔗 Submit Data", use_container_width=True, type="primary")

        if run_forecast:
            try:
                # Validate inputs
                if not self.validate_inputs():
                    return

                # Fetch data
                fetcher = StockDataFetcher()
                data_result = fetcher.fetch_data(
                    self.stock_symbol, self.start_date, self.end_date, self.forecast_end_date
                )
                if data_result is None:
                    return
                fitting_data, forecast_data, fitting_prices, fitting_dates = data_result

                # Filter data
                filterer = StockFiltering()
                filtered_result = filterer.filter_data(fitting_data)
                if filtered_result is None:
                    return
                fitting_prices, fitting_dates = filtered_result

                # Perform fitting
                fitter = StockFitting()
                fitting_result = fitter.perform_fitting(fitting_prices, self.stock_symbol)
                if fitting_result is None:
                    return
                Fitting_S_n_list, v_list, mape_fit = fitting_result

                # Perform forecasting
                forecaster = StockForecasting()
                forecast_result = forecaster.perform_forecasting(
                    Fitting_S_n_list, forecast_data, self.stock_symbol
                )
                S_forecast, forecast_dates, actual_forecast_prices, mape_forecast = forecast_result

                # Display results
                visualizer = StockVisualizer()
                visualizer.display_results(
                    self.stock_symbol, fitting_data, forecast_data, self.start_date, 
                    self.end_date, self.forecast_end_date, fitting_prices, fitting_dates, 
                    Fitting_S_n_list, S_forecast, forecast_dates, actual_forecast_prices, 
                    mape_fit, mape_forecast
                )

                # Export to Excel
                exporter = StockExporter()
                exporter.export_to_excel(
                    self.stock_symbol, fitting_dates, fitting_prices, Fitting_S_n_list, 
                    forecast_dates, S_forecast, actual_forecast_prices, 
                    self.start_date, self.forecast_end_date
                )

            except ValueError as ve:
                st.error(str(ve))
                st.info("Silakan periksa simbol saham di Yahoo Finance atau coba simbol lain.")
            except Exception as e:
                st.error(f"Terjadi kesalahan: {str(e)}")
                logging.error(f"Main execution error: {e}")
                st.info("Silakan coba dengan parameter yang berbeda atau periksa koneksi data.")

def main():
    """Entry point for the application."""
    forecaster = StockForecaster()
    forecaster.run()

if __name__ == "__main__":
    main()