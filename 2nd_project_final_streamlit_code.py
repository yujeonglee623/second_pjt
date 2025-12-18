import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import requests
import zipfile
import io
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="AI 기업 신용 신호등 (Ultimate)", page_icon="🚦", layout="wide")

# 2. 스타일 CSS
st.markdown("""
<style>
    /* 신호등 몸체 (가로형) */
    .traffic-light-body {
        background-color: #333;
        border-radius: 50px;
        padding: 10px 20px;
        display: inline-flex;
        gap: 15px;
        align-items: center;
        border: 4px solid #444;
    }
    /* 신호등 불빛 공통 스타일 */
    .light {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #444; /* 기본 꺼진 상태 (회색) */
        box-shadow: inset 0 0 5px rgba(0,0,0,0.5);
    }
    /* 활성화된 불빛 (강한 빛 효과) */
    .red { background-color: #ff4d4d; box-shadow: 0 0 20px #ff4d4d; }
    .orange { background-color: #ffa500; box-shadow: 0 0 20px #ffa500; }
    .green { background-color: #2ecc71; box-shadow: 0 0 20px #2ecc71; }
    
    .log-text { font-size: 12px; color: #555; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 함수 정의 구역 (호출보다 위에 있어야 함)
# ---------------------------------------------------------

@st.cache_resource
def load_system():
    load_dotenv()
    api_key = os.getenv('DART_API_KEY')
    try:
        model = joblib.load('bankruptcy_model_final_ratio.pkl')
        return api_key, model, "Success"
    except Exception as e:
        return api_key, None, str(e)

@st.cache_data
def get_corp_code_map(api_key):
    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    params = {'crtfc_key': api_key}
    try:
        r = requests.get(url, params=params)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            with z.open('CORPCODE.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                data = []
                for child in root:
                    corp_code = child.find('corp_code').text
                    stock_code = child.find('stock_code').text
                    corp_name = child.find('corp_name').text
                    if stock_code is not None and len(stock_code.strip()) >= 5:
                        data.append({
                            'code': stock_code.strip().zfill(6), # 6자리 강제 맞춤 (005930 등)
                            'dart': corp_code, 
                            'name': corp_name
                        })
        return pd.DataFrame(data)
    except Exception as e:
        return None

def fetch_financial_data(api_key, dart_code, target_year):
    """최신 분기보고서(3분기 -> 반기 -> 1분기) 우선 조회, 없으면 사업보고서 조회"""
    log = []
    
    # 보고서 코드: 3분기(11014), 반기(11012), 1분기(11013), 사업보고서(11011)
    # 유정아, 가장 최신인 3분기부터 순서대로 리스트를 만들었어!
    report_codes = [
        ('11014', '3분기보고서'), 
        ('11012', '반기보고서'), 
        ('11013', '1분기보고서'), 
        ('11011', '사업보고서')
    ]
    
    current_year = datetime.now().year
    # 올해(2025)부터 작년(2024)까지 뒤짐
    for year in [current_year, current_year - 1]:
        for code, name in report_codes:
            url = "https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
            params = {
                'crtfc_key': api_key, 
                'corp_code': dart_code,
                'bsns_year': str(year), 
                'reprt_code': code
            }
            
            try:
                res = requests.get(url, params=params, timeout=5)
                data = res.json()
                
                if data.get('status') == '000':
                    log.append(f"✅ {year}년 {name} 발견")
                    return pd.DataFrame(data['list']), year, name, log
                else:
                    # status가 000이 아니면 데이터가 아직 없는 거니까 로그만 남기고 다음으로!
                    log.append(f"❌ {year}년 {name}: {data.get('message')}")
            except Exception as e:
                log.append(f"⚠️ {year}년 {name} 통신오류: {str(e)}")
    
    return None, None, None, log


def get_audit_opinion(api_key, dart_code, business_year):
    """감사의견 조회 - 실용적 버전"""
    
    try:
        # 1. 기업개황 API 조회
        url = "https://opendart.fss.or.kr/api/company.json"
        params = {'crtfc_key': api_key, 'corp_code': dart_code}
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
        
        if data.get('status') == '000':
            opinion = data.get('adt_opnn', '').strip()
            
            if opinion and opinion not in ['-', 'null', '']:
                opinion = opinion.replace('\n', ' ').strip()
                
                if '의견거절' in opinion or '거절' in opinion:
                    return "의견거절"
                elif '부적정' in opinion:
                    return "부적정"
                elif '한정' in opinion:
                    return "한정"
                elif '적정' in opinion:
                    return "적정"
                else:
                    return opinion[:50]
        
        # 2. 기업개황에 없으면 사업보고서 링크 제공
        report_year = business_year + 1
        list_url = "https://opendart.fss.or.kr/api/list.json"
        list_params = {
            'crtfc_key': api_key,
            'corp_code': dart_code,
            'bgn_de': f'{report_year}0101',
            'end_de': f'{report_year}1231',
            'pblntf_ty': 'A',
            'page_count': 100
        }
        
        list_res = requests.get(list_url, params=list_params, timeout=10)
        list_data = list_res.json()
        
        if list_data.get('status') == '000':
            reports = list_data.get('list', [])
            
            for report in reports:
                report_nm = report.get('report_nm', '')
                if '사업보고서' in report_nm and '정정' not in report_nm:
                    rcept_no = report.get('rcept_no')
                    # ✅ 사용자가 직접 확인하도록 링크 제공
                    return f"미제공 ({business_year}년 사업보고서 제출됨)"
        
        return "정보 없음"
        
    except Exception as e:
        return "조회 실패"

def get_corp_status(api_key, dart_code):
    """기업 개황 정보를 통해 업종명과 업종코드를 가져옴"""
    url = "https://opendart.fss.or.kr/api/company.json"
    params = {'crtfc_key': api_key, 'corp_code': dart_code}
    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
        if data.get('status') == '000':
            return data
    except:
        return None
    return None

def get_val_ts(df_in, kws):
    for k in kws:
        rows = df_in[df_in['account_nm'].str.replace(' ', '').str.contains(k, na=False)]
        if not rows.empty:
            val = str(rows.iloc[0]['thstrm_amount']).replace(',', '').strip()
            return float(val) if val else 0.0
    return 0.0

def get_similar_recommends(api_key, corp_map_df, current_corp_name, current_industry_code, limit=4):
    """같은 업종 코드 기업 중 안정성 높은 기업 추천 (앞 2자리 매칭)"""
    
    if not current_industry_code or current_industry_code == '알수없음':
        st.info("🔍 업종 정보가 없어 전체 기업에서 추천합니다.")
        candidates = corp_map_df[corp_map_df['name'] != current_corp_name].sample(min(15, len(corp_map_df)))
    else:
        # ✅ 업종 코드 앞 2자리 추출 (대분류)
        industry_prefix = current_industry_code[:2] if len(current_industry_code) >= 2 else current_industry_code
        
        st.info(f"🔍 업종 대분류 {industry_prefix}로 시작하는 기업을 검색 중...")
        same_industry = []
        
        # 샘플 150개로 확대 (앞 2자리만 매칭하니 더 많이 체크)
        sample_size = min(150, len(corp_map_df) - 1)
        sample_corps = corp_map_df[corp_map_df['name'] != current_corp_name].sample(sample_size)
        
        checked_count = 0
        for _, row in sample_corps.iterrows():
            try:
                url = "https://opendart.fss.or.kr/api/company.json"
                params = {'crtfc_key': api_key, 'corp_code': row['dart']}
                res = requests.get(url, params=params, timeout=2)
                data = res.json()
                
                checked_count += 1
                
                if data.get('status') == '000':
                    induty_code = data.get('induty_code', '')
                    
                    # ✅ 앞 2자리만 비교
                    if induty_code and induty_code[:2] == industry_prefix:
                        same_industry.append(row)
                        
                        if len(same_industry) >= 20:
                            break
                
                # 진행상황 표시 (매 30개마다)
                if checked_count % 30 == 0:
                    st.text(f"📊 {checked_count}개 검색 완료... (발견: {len(same_industry)}개)")
                    
            except:
                continue
        
        if len(same_industry) >= 5:
            st.success(f"✅ 유사 업종 기업 {len(same_industry)}개 발견 (업종코드 {industry_prefix}XX)")
            candidates = pd.DataFrame(same_industry)
        else:
            st.warning(f"⚠️ 유사 업종 기업이 {len(same_industry)}개뿐이어서 전체에서 추천합니다.")
            candidates = corp_map_df[corp_map_df['name'] != current_corp_name].sample(min(20, len(corp_map_df)))
    
    # 재무 분석
    recom_results = []
    for _, row in candidates.iterrows():
        try:
            df_sub, f_y, r_n, _ = fetch_financial_data(api_key, row['dart'], datetime.now().year - 1)
            
            if df_sub is not None:
                df_t = df_sub[df_sub['fs_div'] == 'CFS'] if 'fs_div' in df_sub.columns and not df_sub[df_sub['fs_div'] == 'CFS'].empty else df_sub
                a = get_val_ts(df_t, ['자산총계'])
                l = get_val_ts(df_t, ['부채총계'])
                e = get_val_ts(df_t, ['자본총계'])
                s = get_val_ts(df_t, ['매출액'])
                
                if e != 0 and a != 0 and s != 0:
                    d_r = (l / e) * 100
                    o_m = (get_val_ts(df_t, ['영업이익']) / s) * 100
                    n_m = (get_val_ts(df_t, ['당기순이익']) / s) * 100
                    roa_v = (get_val_ts(df_t, ['당기순이익']) / a) * 100
                    
                    in_df = pd.DataFrame({'부채비율': [d_r], '영업이익률': [o_m], '순이익률': [n_m], 'ROA': [roa_v]})
                    prob = model.predict_proba(in_df)[0][1] * 100
                    
                    recom_results.append({
                        'name': row['name'],
                        'code': row['code'],
                        'prob': prob,
                        'debt': d_r
                    })
                    
                if len(recom_results) >= limit + 2:
                    break
        except Exception as e:
            continue
    
    return sorted(recom_results, key=lambda x: x['prob'])[:limit]

# ---------------------------------------------------------
# 4. 시스템 로드 및 사이드바
# ---------------------------------------------------------
api_key, model, status = load_system()
corp_map_df = None

if api_key:
    with st.sidebar:
        with st.spinner("📡 기업 리스트 로딩 중..."):
            corp_map_df = get_corp_code_map(api_key)
            
    # 사이드바 종목 검색창
    st.sidebar.markdown("### 🔍 종목 찾기")
    search_query = st.sidebar.text_input("종목명 입력", placeholder="예: 삼성전자", key="sidebar_search")
    if search_query and corp_map_df is not None:
        search_results = corp_map_df[corp_map_df['name'].str.contains(search_query, na=False, case=False)]
        if not search_results.empty:
            st.sidebar.info(f"📌 '{search_query}' 검색결과")
            for i, row in search_results.head(5).iterrows():
                st.sidebar.code(f"{row['code']}  # {row['name']}")
        else:
            st.sidebar.error("❌ 일치하는 종목 없음")

st.sidebar.divider()
st.sidebar.title("🚦 AI Credit Monitor")
st.sidebar.divider()

if status == "Success":
    st.sidebar.subheader("📡 엔진 상태")
    st.sidebar.success("AI 모델 로드 완료")
    if st.sidebar.button("🔄 시스템 리셋", use_container_width=True):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()
else:
    st.sidebar.error(f"🚨 시스템 오류: {status}")

# ---------------------------------------------------------
# 5. 메인 화면
# ---------------------------------------------------------
st.title("🚦 기업 부도 위험 진단")
st.info("💡 사이드바에서 종목명을 검색해 코드를 확인한 뒤 입력하세요.")

col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_input("종목코드 입력", placeholder="예: 005930")
with col2:
    st.write("") ; st.write("")
    search_btn = st.button("🔍 진단 시작", use_container_width=True)

# 버튼 클릭 전에도 변수가 존재하도록 미리 선언해줘!
industry_name = "해당" 
dart_code = None
corp_name = None

if search_btn and user_input:
    if corp_map_df is None:
        st.error("기업 리스트가 로드되지 않았습니다.")
        st.stop()
    
    # ✅ 입력값 정규화 (공백 제거 + 6자리 패딩)
    user_input_clean = user_input.strip().zfill(6)
    
    found = corp_map_df[corp_map_df['code'] == user_input_clean]
    
    if found.empty:
        st.error(f"❌ 종목코드 '{user_input_clean}'을 찾을 수 없습니다.")
        st.info("💡 **사이드바에서 종목명으로 검색**해 정확한 6자리 코드를 확인해주세요.")
        
        # 유사 코드 제안
        if len(user_input.strip()) > 0:
            similar = corp_map_df[corp_map_df['code'].str.contains(user_input.strip())]
            if not similar.empty:
                st.write("🔍 **입력하신 숫자가 포함된 종목:**")
                for _, row in similar.head(5).iterrows():
                    st.code(f"{row['code']}  # {row['name']}")
        st.stop()
        
    dart_code = found.iloc[0]['dart']
    corp_name = found.iloc[0]['name']
    
    # ✅ 업종명 가져오기
    industry_code = None
    industry_name = "동일 업종"
    
    corp_info = get_corp_status(api_key, dart_code)
    if corp_info:
        # induty_code는 숫자 코드 (예: 201)
        industry_code = corp_info.get('induty_code', '알수없음')
        # induty_nm은 실제 이름 (예: 기초 화학물질 제조업)
        industry_name = corp_info.get('induty_nm', f"업종코드 {industry_code}")
    
    # 데이터 스캔
    with st.spinner(f"📡 '{corp_name}' 분석 중..."):
        current_year = datetime.now().year
        
        # ✅ fetch_financial_data는 이미 최신 사업보고서를 찾아줌
        df, found_year, report_name, logs = fetch_financial_data(api_key, dart_code, current_year)
        
        # 2. 재무 데이터 스캔 결과 처리
        if df is not None:
            audit_result = get_audit_opinion(api_key, dart_code, found_year)
            
            # --- 기존 데이터 추출 로직들 ---
            df_t = df[df['fs_div'] == 'CFS'] if 'fs_div' in df.columns and not df[df['fs_div'] == 'CFS'].empty else df
            assets = get_val_ts(df_t, ['자산총계'])
            # ... (중략) ...

            # --- 심층 분석 리포트 구역 (전체 가로폭 사용!) ---
            st.write("") 
            with st.container():

                # [기본 데이터 추출 및 비율 계산] - (이 부분은 유정이 코드와 동일)
                df_t = df[df['fs_div'] == 'CFS'] if 'fs_div' in df.columns and not df[df['fs_div'] == 'CFS'].empty else df
                assets = get_val_ts(df_t, ['자산총계'])
                liabilities = get_val_ts(df_t, ['부채총계'])
                equity = get_val_ts(df_t, ['자본총계'])
                sales = get_val_ts(df_t, ['매출액', '영업수익', '수익(매출액)'])
                op_profit = get_val_ts(df_t, ['영업이익'])
                net_profit = get_val_ts(df_t, ['당기순이익'])

                debt_ratio = (liabilities / equity * 100) if equity != 0 else 999
                op_margin = (op_profit / sales * 100) if sales != 0 else 0
                net_margin = (net_profit / sales * 100) if sales != 0 else 0
                roa = (net_profit / assets * 100) if assets != 0 else 0

                input_df = pd.DataFrame({'부채비율': [debt_ratio], '영업이익률': [op_margin], '순이익률': [net_margin], 'ROA': [roa]})
                risk_prob = model.predict_proba(input_df)[0][1] * 100

                reasons = []
                if debt_ratio > 200: reasons.append("부채비율 200% 초과 (재무 건전성 악화)")
                if op_margin < 0: reasons.append("영업이익 적자 (수익성 저하)")
                if net_margin < 0: reasons.append("당기순이익 적자 (결손금 누적)")

                # ---------------------------------------------------------
                # 5. 결과 시각화
                st.divider()
                st.subheader(f"📊 {corp_name} ({found_year}년 {report_name})")
                
                # [A] 상단 구역: 신호등(좌) + 핵심지표(우)
                col_top_left, col_top_right = st.columns([1.5, 2])
                
                with col_top_left:
                    # 신호등 로직
                    if risk_prob < 10.0:
                        red_class, orange_class, green_class = "", "", "green"
                        status_text, status_color = "안전", "#2ecc71"
                    elif risk_prob < 70.0:
                        red_class, orange_class, green_class = "", "orange", ""
                        status_text, status_color = "주의", "#f39c12"
                    else:
                        red_class, orange_class, green_class = "red", "", ""
                        status_text, status_color = "위험", "#e74c3c"
                    
                    traffic_html = f"""
                    <div style="text-align:center; padding: 10px 0px;">
                        <div class="traffic-light-body">
                            <div class="light {red_class}"></div>
                            <div class="light {orange_class}"></div>
                            <div class="light {green_class}"></div>
                        </div>
                        <p style="margin-top:10px; font-size:24px; font-weight:bold; color:{status_color};">{status_text}</p>
                    </div>
                    """
                    st.markdown(traffic_html, unsafe_allow_html=True)

                with col_top_right:
                    # [진단 결과 텍스트]
                    if risk_prob < 10.0: t, info_type = "안전", "success"
                    elif risk_prob < 70.0: t, info_type = "주의", "warning"
                    else: t, info_type = "위험", "error"
                    
                    st.info(f"**진단결과: {t}**")
                    st.write(f"부도 확률 예측: **{risk_prob:.2f}%**")

                    if reasons:
                        with st.expander("🧐 주요 위험 요인 분석"):
                            for r in reasons:
                                st.write(f"• {r}")

            # [B] 하단 구역: 감사의견, 심층 분석 리포트 (전체 가로폭 사용!)
            st.write("") # 약간의 여백
            with st.container():
                st.markdown("### 🧐 AI 심층 분석 리포트")
                
                # 1. 감사의견을 전체 가로폭으로 먼저 배치 (rc1, rc2 나누기 전!)
                # audit_result 값은 위에서 미리 받아왔다고 가정할게!
                # 여기서 이제 audit_result를 마음껏 쓸 수 있어!
                if "정보 없음" in audit_result or "조회 실패" in audit_result:
                    bg_color = "#f0f2f6"
                    border_color = "#bdc3c7"
                    text_color = "#7f8c8d"
                    icon = "⚪"
                    msg = f"<b>감사의견 ({found_year}년 기준):</b> {audit_result} — 감사의견 정보를 확인할 수 없습니다."
                elif "적정" in audit_result:
                    bg_color = "#e8f4f8"
                    border_color = "#3498db"
                    text_color = "#2980b9"
                    icon = "🔵"
                    msg = f"<b>감사의견 ({found_year}년 기준):</b> {audit_result} — 회계 투명성이 확인되었습니다. 재무제표를 신뢰할 수 있습니다."
                elif "한정" in audit_result:
                    bg_color = "#fff3cd"
                    border_color = "#f39c12"
                    text_color = "#856404"
                    icon = "🟡"
                    msg = f"<b>감사의견 ({found_year}년 기준):</b> {audit_result} — 일부 회계처리에 한정사항이 있습니다. 주의가 필요합니다."
                else:  # 부적정, 의견거절 등
                    bg_color = "#fdecea"
                    border_color = "#e74c3c"
                    text_color = "#c0392b"
                    icon = "🔴"
                    msg = f"<b>감사의견 ({found_year}년 기준):</b> {audit_result} — 심각한 회계 문제가 발견되었습니다. 투자에 각별한 주의가 필요합니다."
                
                # 2. 커스텀 HTML 박스 출력
                st.markdown(f"""
                    <div style="
                        background-color: {bg_color};
                        border-left: 5px solid {border_color};
                        padding: 15px;
                        border-radius: 5px;
                        color: {text_color};
                        margin-bottom: 20px;
                    ">
                        <span style="font-size: 20px; margin-right: 10px;">{icon}</span>
                        {msg}
                    </div>
                """, unsafe_allow_html=True)
                
                st.write("") # 감사의견과 하단 리포트 사이 살짝 여백
                # 넓게 깔아주는 리포트 칸
                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown("#### 🔍 재무 건전성 요약")
                    if debt_ratio > 200: 
                        st.error(f"⚠️ **부채비율({debt_ratio:.1f}%) 높음**: 타인 자본 의존도가 높아 재무 구조 개선이 시급합니다.")
                    else: 
                        st.success(f"✅ **부채비율({debt_ratio:.1f}%) 안정**: 매우 건전한 자본 구조를 가지고 있어 외부 충격에 강합니다.")
                    
                    if op_margin < 0: 
                        st.error(f"⚠️ **영업적자({op_margin:.1f}%)**: 본업에서 손실이 발생하고 있어 경쟁력 확보가 필요합니다.")
                    else: 
                        st.success(f"✅ **영업이익률({op_margin:.1f}%)**: 안정적인 영업 활동을 통해 꾸준한 수익을 창출하고 있습니다.")
                
                with rc2:
                    st.markdown("#### ⚖️ 기업 유형 진단")
                    if debt_ratio <= 100 and op_margin >= 5: 
                        st.info("🌟 **[초우량 기업]**\n\n돈도 잘 벌고 빚도 없는 완벽한 상태입니다. 투자 가치가 매우 높은 'Cash Cow'형 기업입니다.")
                    elif debt_ratio <= 100 and op_margin < 5: 
                        st.warning("💰 **[자산가형 기업]**\n\n수익성은 다소 낮으나 재무적으로 매우 안정적입니다. 당장의 위기에는 강한 타입입니다.")
                    elif debt_ratio > 100 and op_margin >= 5: 
                        st.warning("🏃 **[성장형 기업]**\n\n부채를 레버리지로 활용해 높은 수익을 내고 있습니다. 공격적인 투자가 진행 중인 상태입니다.")
                    else: 
                        st.error("🚨 **[위험군 기업]**\n\n수익성이 낮은데 빚까지 많아 구조조정이 시급할 수 있습니다. 각별한 주의가 필요합니다.")

                # --- [2] 핵심 지표 메트릭 (차트 바로 위로 이동!) ---
                st.write("") # 리포트와 메트릭 사이 여백
                st.divider() # 얇은 구분선 하나 넣어주면 더 깔끔해!
                cols = st.columns(4)
                cols[0].metric("부채비율", f"{debt_ratio:.1f}%")
                cols[1].metric("영업이익률", f"{op_margin:.1f}%")
                cols[2].metric("순이익률", f"{net_margin:.1f}%")
                cols[3].metric("ROA", f"{roa:.1f}%")

            # [5개년 트렌드 차트]
            st.divider()
            st.subheader("📈 최근 5개년 재무 추이")
            
            # ✅ 변수 선언
            years_to_check = [found_year - i for i in range(0, 5)]
            ts_results = []
            
            for y in years_to_check:
                # 각 연도별로 사업보고서 조회
                url = "https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
                params = {
                    'crtfc_key': api_key,
                    'corp_code': dart_code,
                    'bsns_year': str(y),
                    'reprt_code': '11011'
                }
                
                try:
                    res = requests.get(url, params=params, timeout=5)
                    data = res.json()
                    
                    if data.get('status') == '000':
                        df_y = pd.DataFrame(data['list'])
                        df_target = df_y[df_y['fs_div'] == 'CFS'] if 'fs_div' in df_y.columns and not df_y[df_y['fs_div'] == 'CFS'].empty else df_y
                        
                        ts_results.append({
                            'year': y,
                            'sales': get_val_ts(df_target, ['매출액', '영업수익']) / 100000000,
                            'equity': get_val_ts(df_target, ['자본총계']) / 100000000,
                            'debt': get_val_ts(df_target, ['부채총계']) / 100000000
                        })
                except:
                    pass

            if ts_results and len(ts_results) >= 2:
                df_ts = pd.DataFrame(ts_results).sort_values('year')
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_ts['year'], 
                    y=df_ts['sales'], 
                    name='매출(억)', 
                    marker_color='rgba(52, 152, 219, 0.6)'
                ))
                fig.add_trace(go.Scatter(
                    x=df_ts['year'], 
                    y=df_ts['equity'], 
                    name='자본(억)', 
                    line=dict(color='green', width=3),
                    mode='lines+markers'
                ))
                fig.add_trace(go.Scatter(
                    x=df_ts['year'], 
                    y=df_ts['debt'], 
                    name='부채(억)', 
                    line=dict(color='red', width=3),
                    mode='lines+markers'
                ))
                
                fig.update_layout(
                    title=f"최근 {len(ts_results)}개년 재무 추이",
                    xaxis_title="연도",
                    yaxis_title="금액 (억원)",
                    hovermode="x unified",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"⚠️ 차트 표시를 위한 충분한 데이터가 없습니다. (조회된 연도: {len(ts_results)}개)")

            # 7. 실시간 우량 종목 추천 (유정이가 말한 핵심 기능!)
        st.divider()
        st.subheader(f"🌟 '{corp_name}' 대비 안정성이 높은 추천 기업")
        
        if industry_code and industry_code != '알수없음':
            st.caption(f"업종 코드 {industry_code}({industry_name}) 내 기업들을 분석하여 재무 안정성이 높은 기업을 선별했습니다.")
        else:
            st.caption("상장 기업들을 분석하여 재무 안정성이 높은 기업을 선별했습니다.")
        
        with st.spinner("🚀 실시간 기업 분석 중..."):
            recoms = get_similar_recommends(api_key, corp_map_df, corp_name, industry_code)
            
            if recoms:
                rec_cols = st.columns(4)
                for idx, item in enumerate(recoms):
                    with rec_cols[idx]:
                        # 카드 형태로 예쁘게 출력
                        st.markdown(f"""
                        <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; border-top:5px solid #2ecc71;">
                            <h4 style="margin:0;">{item['name']}</h4>
                            <code style="font-size:12px;">{item['code']}</code>
                            <p style="margin:10px 0 0 0; font-size:14px; color:#555;">부도 위험도</p>
                            <h3 style="margin:0; color:#2ecc71;">{item['prob']:.1f}%</h3>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.write("유사 기업 데이터를 불러오는 데 실패했습니다.")