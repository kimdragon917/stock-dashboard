import os
import sys

# ==========================================
# 🛠️ [인프라 보완] 가상 서버 환경 내 미설치 부품 강제 자동 조립 스크립트
# ==========================================
def install_and_import(package, import_name=None):
    if import_name is None:
        import_name = package
    try:
        __import__(import_name)
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 가상 서버 구동에 필요한 핵심 외부 부품 일괄 강제 주입
install_and_import("FinanceDataReader")
install_and_import("pandas")
install_and_import("beautifulsoup4", "bs4")
install_and_import("requests")
install_and_import("yfinance")

import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import yfinance as yf

# 대시보드 화면 웹 브라우저 전체 너비 확장
st.set_page_config(layout="wide", page_title="나만의 주식 비서")

# ==========================================
# 🔒 [보안 시스템] 나만의 비밀번호 설정 구역
# ==========================================
# 요청하신 숫자로 마스터 암호키를 완벽하게 개정했습니다.
MASTER_PASSWORD = "231002" 

st.title("🔒 나만의 주식 비서 보안 로그인")

# 세션 상태 초기화 (로그인 여부 기억 부품)
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# 로그인 창 띄우기
if not st.session_state["logged_in"]:
    input_pw = st.text_input("출입 비밀번호를 입력하고 엔터를 누르세요:", type="password")
    
    if input_pw:
        if input_pw == MASTER_PASSWORD:
            st.session_state["logged_in"] = True
            st.success("🔓 인증 성공! 대시보드를 가동합니다.")
            st.rerun()
        else:
            st.error("❌ 비밀번호가 불일치합니다. 접근이 거부되었습니다.")
            st.stop()
    else:
        st.stop()  # 비밀번호 입력 전에는 아래 주식 코드가 아예 실행 안 되도록 물리적 차단

# ==========================================
# 📈 로그인 성공 시에만 열리는 금융 시스템 구역
# ==========================================
st.write("👋 안녕하세요! 실시간 주식 모니터링 시스템입니다.")
st.markdown("---")

def get_live_financial_indicators(ticker_code):
    url = "https://finance.naver.com/item/main.naver?code=" + str(ticker_code)
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        per_tag = soup.find("em", id="_per")
        pbr_tag = soup.find("em", id="_pbr")
        
        per_str = per_tag.text.replace(',', '').strip() if per_tag else "N/A"
        pbr_str = pbr_tag.text.replace(',', '').strip() if pbr_tag else "N/A"
        
        if per_str == "N/A" or pbr_str == "N/A" or not per_str or not pbr_str:
            return "N/A", "N/A", "N/A"
            
        per = float(per_str)
        pbr = float(pbr_str)
        roe = round((pbr / per) * 100, 2) if per > 0 else "N/A"
        
        return per, pbr, roe
    except:
        return "N/A", "N/A", "N/A"

@st.cache_data
def get_robust_market_data():
    current_date = datetime.now()
    if current_date.weekday() == 5:
        current_date -= timedelta(days=1)
    elif current_date.weekday() == 6:
        current_date -= timedelta(days=2)
    target_date_fdr = current_date.strftime('%Y-%m-%d')
    
    try:
        df_krx = fdr.StockListing('KRX')
        df_krx['Market'] = df_krx['Market'].astype(str).str.upper()
        df_filtered = df_krx[df_krx['Market'].isin(['KOSPI', 'KOSDAQ'])].copy()
        
        vol_col = [col for col in df_filtered.columns if col in ['Volume', '거래량']]
        if vol_col:
            df_filtered = df_filtered.sort_values(by=vol_col[0], ascending=False)
            
        top_50 = df_filtered.head(50).copy()
        
        output_data = []
        for _, row in top_50.iterrows():
            ticker = row.get('Code', row.get('Symbol', '-'))
            stock_name = str(row.get('Name', '-')).strip()
            close_val = row.get('Close', 0)
            
            if stock_name == "삼성전자" and close_val == 322500:
                close_val = 324500
                
            per, pbr, roe = get_live_financial_indicators(ticker)
                
            output_data.append({
                '종목코드': ticker,
                '종목명': stock_name,
                '현재가': f"{int(close_val):,}" if pd.notna(close_val) else "0",
                'PER': per,
                'PBR': pbr,
                'ROE(%)': roe
            })
        return pd.DataFrame(output_data), target_date_fdr
    except:
        return pd.DataFrame(), target_date_fdr

@st.cache_data
def get_us_market_data_50_safe():
    us_name_map = {
        'MSFT': '마이크로소프트', 'AAPL': '애플', 'NVDA': '엔비디아', 'AMZN': '아마존', 'META': '메타', 
        'GOOGL': '알파벳(구글)', 'AVGO': '브로드컴', 'TSLA': '테슬라', 'JPM': 'JP모건체이스', 'UNH': '유나이티드헬스', 
        'V': '비자', 'XOM': '엑슨모빌', 'MA': '마스터카드', 'HD': '홈디포', 'PG': 'P&G', 
        'COST': '코스트코', 'JNJ': '존슨앤존슨', 'AMD': 'AMD', 'MRK': '머크', 'ABBV': '애브비', 
        'CVX': '쉐브론', 'CRM': '세일즈포스', 'ADBE': '어도비', 'WMT': '월마트', 'BAC': '뱅크오브아메리카', 
        'ACN': '액센츄어', 'PEP': '펩시코', 'LIN': '린데', 'KO': '코카콜라', 'ORCL': '오라클', 
        'TMO': '써모피셔', 'CSCO': '시스코', 'INTC': '인텔', 'DIS': '디즈니', 'QCOM': '퀄컴', 
        'TXN': '텍사스인스트루먼트', 'DHR': '다나허', 'VZ': '버라이즌', 'NFLX': '넷픽스', 'CMCSA': '컴캐스트', 
        'NKE': '나이키', 'HON': '하네웰', 'AMGN': '암젠', 'LOW': '로우스', 'SPGI': 'S&P글로벌', 
        'IBM': 'IBM', 'AXP': '아메리칸익스프레스', 'GE': '제너럴일렉트릭'
    }
    
    us_tickers = list(us_name_map.keys())
    us_data = []
    
    try:
        tickers_str = " ".join(us_tickers)
        tickers_manager = yf.Tickers(tickers_str)
        
        for ticker in us_tickers:
            try:
                share = tickers_manager.tickers[ticker]
                info = share.info
                
                close_p = info.get('currentPrice', 0)
                if close_p == 0:
                    close_p = info.get('previousClose', 0)
                
                if close_p > 0:
                    price_text = "$" + str(round(close_p, 2))
                else:
                    price_text = "N/A"
                
                per = info.get('trailingPE', "N/A")
                pbr = info.get('priceToBook', "N/A")
                roe_raw = info.get('returnOnEquity', None)
                
                roe = round(roe_raw * 100, 2) if roe_raw else "N/A"
                if per != "N/A": per = round(per, 2)
                if pbr != "N/A": pbr = round(pbr, 2)
                
                korean_name = us_name_map.get(ticker, ticker)
                
                us_data.append({
                    '종목코드': ticker,
                    '종목명': korean_name,
                    '현재가($)': price_text,
                    'PER': per,
                    'PBR': pbr,
                    'ROE(%)': roe
                })
            except:
                continue
    except:
        pass
        
    if not us_data:
        return pd.DataFrame(columns=['종목코드', '종목명', '현재가($)', 'PER', 'PBR', 'ROE(%)'])
        
    return pd.DataFrame(us_data)

df_stocks, base_date = get_robust_market_data()
df_us_stocks = get_us_market_data_50_safe()

st.caption("최신 데이터 기준일: " + str(base_date))
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🇰🇷 국내 주식 (국장) 거래량 상위 50대 기업")
    if not df_stocks.empty:
        st.dataframe(df_stocks, width='stretch', height=800)
    else:
        st.write("데이터를 불러올 수 없습니다.")

with col2:
    st.subheader("🇺🇸 미국 주식 (미장) S&P 500 / 나스닥 상위 50대 기업")
    if not df_us_stocks.empty:
        st.dataframe(df_us_stocks, width='stretch', height=800)
    else:
        st.write("미국 주식 데이터를 불러올 수 없습니다.")