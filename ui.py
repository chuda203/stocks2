import streamlit as st
from datetime import datetime, timedelta

def create_ui():
    st.title("📈 Stock Price Fitting and Forecasting Web")
    st.markdown("---")
    
    # Input Parameter
    st.subheader("📋 Input Parameter")
    
    # Initialize session state for reset flag and start_date tracking
    if 'reset_inputs' not in st.session_state:
        st.session_state.reset_inputs = False
    if 'last_start_date' not in st.session_state:
        st.session_state.last_start_date = None
    
    # Create 4 columns for the input fields
    col1, col2, col3, col4 = st.columns(4)
    
    # Default values
    default_stock_symbol = "BBCA.JK"
    today = datetime.today().date()
    max_fitting_date = today - timedelta(days=2)
    default_start_date = today - timedelta(days=120)  
    default_training_days = 120  
    default_forecast_days = 60
    default_custom_end_date = max_fitting_date
    default_forecast_end_date = max_fitting_date + timedelta(days=default_forecast_days)
    
    # Clear All function
    def clear_all():
        st.session_state.stock_input = default_stock_symbol
        st.session_state.start_date_input = default_start_date
        max_training_days_for_default = (max_fitting_date - default_start_date).days
        st.session_state.training_days = min(default_training_days, max(1, max_training_days_for_default))
        st.session_state.forecast_days = default_forecast_days
        st.session_state.use_custom_end = False
        st.session_state.custom_end = default_custom_end_date
        st.session_state.use_custom_forecast_end = False
        st.session_state.custom_forecast_end = default_forecast_end_date
        st.session_state.last_start_date = default_start_date
    
    # Use default values if reset is triggered
    if st.session_state.reset_inputs:
        stock_symbol_value = default_stock_symbol
        start_date_value = default_start_date
        max_training_days_for_default = max(1, (max_fitting_date - default_start_date).days)
        training_days_value = min(default_training_days, max_training_days_for_default)
        forecast_days_value = default_forecast_days
        use_custom_end_value = False
        use_custom_forecast_end_value = False
        custom_end_date_value = default_custom_end_date
        custom_forecast_end_value = default_forecast_end_date
    else:
        # Use current session state or defaults for initial load
        stock_symbol_value = st.session_state.get('stock_input', default_stock_symbol)
        start_date_value = st.session_state.get('start_date_input', default_start_date)
        forecast_days_value = st.session_state.get('forecast_days', default_forecast_days)
        use_custom_end_value = st.session_state.get('use_custom_end', False)
        use_custom_forecast_end_value = st.session_state.get('use_custom_forecast_end', False)
        custom_end_date_value = st.session_state.get('custom_end', default_custom_end_date)
        custom_forecast_end_value = st.session_state.get('custom_forecast_end', default_forecast_end_date)
    
    with col1:
        st.markdown("**Stock Symbol**")
        stock_symbol = st.text_input(
            "", 
            value=stock_symbol_value, 
            key="stock_input", 
            label_visibility="collapsed",
            help="Masukkan simbol saham (contoh: BBCA.JK untuk saham Indonesia). Cek simbol valid di: https://finance.yahoo.com/lookup"
        ).upper()    
        
    with col2:
        st.markdown("**Fitting Start Date**")
        start_date = st.date_input(
            "", 
            value=start_date_value, 
            max_value=max_fitting_date,
            key="start_date_input", 
            label_visibility="collapsed",
            help=f"Tanggal mulai tidak boleh melebihi {max_fitting_date.strftime('%d/%m/%Y')} (2 hari sebelum hari ini: {today.strftime('%d/%m/%Y')})."
        )
    
    with col3:
        st.markdown("**Fitting Period (Day)**")
        max_training_days = max(1, (max_fitting_date - start_date).days)
        # Adjust training_days_value if start_date has changed
        if st.session_state.last_start_date != start_date:
            training_days_value = min(st.session_state.get('training_days', default_training_days), max_training_days)
            st.session_state.training_days = training_days_value
            st.session_state.last_start_date = start_date
        else:
            training_days_value = st.session_state.get('training_days', min(default_training_days, max_training_days))
        training_days = st.number_input(
            "", 
            min_value=1, 
            max_value=max_training_days, 
            value=training_days_value, 
            step=1, 
            key="training_days", 
            label_visibility="collapsed",
            help=f"Periode fitting maksimum {max_training_days} hari hingga {max_fitting_date.strftime('%d/%m/%Y')}."
        )
    
    with col4:
        st.markdown("**Forecast Period (Day)**")
        forecast_days = st.number_input(
            "", 
            min_value=1, 
            value=forecast_days_value, 
            step=1, 
            key="forecast_days", 
            label_visibility="collapsed",
            help="Masukkan jumlah hari untuk periode forecast."
        )
    
    # Clear All Button 
    st.button("🗑️ Clear All", on_click=clear_all, use_container_width=True)
    
    # Calculate end_date based on training_days
    end_date = start_date + timedelta(days=training_days)
    if end_date > max_fitting_date:
        end_date = max_fitting_date
        training_days = max(1, (end_date - start_date).days)
    
    # Calculate forecast_end_date
    forecast_end_date = end_date + timedelta(days=forecast_days)
    
    # Advanced Options (Collapsible)
    with st.expander("⚙️ Advanced Options"):
        col_adv1, col_adv2 = st.columns(2)
        
        with col_adv1:
            use_custom_end = st.checkbox("Custom Fitting End Date", value=use_custom_end_value, key="use_custom_end")
            if use_custom_end:
                st.markdown("**Custom Fitting End Date**")
                custom_end_date = st.date_input(
                    "", 
                    value=custom_end_date_value, 
                    max_value=max_fitting_date,
                    min_value=start_date, 
                    key="custom_end", 
                    label_visibility="collapsed",
                    help=f"Tanggal akhir fitting tidak boleh melebihi {max_fitting_date.strftime('%d/%m/%Y')} (2 hari sebelum hari ini: {today.strftime('%d/%m/%Y')})."
                )
                end_date = custom_end_date
                training_days = max(1, (end_date - start_date).days)
        
        with col_adv2:
            use_custom_forecast_end = st.checkbox("Custom Forecast End Date", value=use_custom_forecast_end_value, key="use_custom_forecast_end")
            if use_custom_forecast_end:
                st.markdown("**Custom Forecast End Date**")
                custom_forecast_end = st.date_input(
                    "", 
                    value=custom_forecast_end_value, 
                    min_value=end_date,
                    key="custom_forecast_end", 
                    label_visibility="collapsed",
                    help="Pilih tanggal akhir untuk periode forecast."
                )
                forecast_end_date = custom_forecast_end
                forecast_days = max(1, (forecast_end_date - end_date).days)
    
    # Reset the reset_inputs flag after applying values
    if st.session_state.reset_inputs:
        st.session_state.reset_inputs = False
    
    # Ringkasan Input
    col_summary1, col_summary2 = st.columns(2)
    
    with col_summary1:
        st.markdown(f"""
        **📊 Fitting Period Details:**
        - **Periode Fitting:** {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}
        - **Durasi Fitting:** {training_days} hari
        """)
    
    with col_summary2:
        st.markdown(f"""
        **🔮 Data Forecast Period Details:**
        - **Periode Forecast:** {end_date.strftime('%d/%m/%Y')} - {forecast_end_date.strftime('%d/%m/%Y')}
        - **Durasi Forecast:** {forecast_days} hari
        """)
    
    # Warning for short fitting periods
    if training_days < 4:
        st.warning("⚠️ Fitting period kurang dari 4 hari. Minimal 4 hari diperlukan untuk forecasting yang akurat.")
    
    st.markdown("---")
    
    return stock_symbol, start_date, training_days, forecast_days, end_date, forecast_end_date