import numpy as np
import pandas as pd
import streamlit as st
from sklearn.cluster import KMeans
from datetime import datetime
from PIL import Image
from io import BytesIO

st.set_page_config(page_title='RFV',
    layout="wide",
    initial_sidebar_state='expanded'
)

st.write("""# RFV

RFV significa recência, frequência, valor e é utilizado para segmentação de clientes baseado no comportamento 
de compras dos clientes e agrupa eles em clusters parecidos. Utilizando esse tipo de agrupamento podemos realizar 
ações de marketing e CRM melhores direcionadas, ajudando assim na personalização do conteúdo e até a retenção de clientes.

Para cada cliente é preciso calcular cada uma das componentes abaixo:

- Recência (R): Quantidade de dias desde a última compra.
- Frequência (F): Quantidade total de compras no período.
- Valor (V): Total de dinheiro gasto nas compras do período.

E é isso que iremos fazer abaixo.
""")
st.markdown("---")

@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_file = output.getvalue()
    return processed_file

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

@st.cache_data
def recencia_class(x, r, q_dict):
    if x <= q_dict[r][0.25]:
        return 'A'
    if x <= q_dict[r][0.5]:
        return 'B'
    if x <= q_dict[r][0.75]:
        return 'C'
    else:
        return 'D'

@st.cache_data
def freq_val_class(x, fv, q_dict):
    if x <= q_dict[fv][0.25]:
        return 'D'
    if x <= q_dict[fv][0.5]:
        return 'C'
    if x <= q_dict[fv][0.75]:
        return 'B'
    else:
        return 'A'

def main():
    st.sidebar.write("## Suba o arquivo")
    data_file_1 = st.sidebar.file_uploader("Bank marketing data", type=['csv', 'xlsx'])

    if data_file_1 is not None:
        df_compras = pd.read_csv(data_file_1, infer_datetime_format=True, parse_dates=['DiaCompra'])

        st.write('## Recência (R)')
        min_data = df_compras['DiaCompra'].min()
        max_data = df_compras['DiaCompra'].max()

        data_inicial = st.sidebar.date_input('Data inicial',
                                             value=min_data,
                                             min_value=min_data,
                                             max_value=max_data)
        data_final = st.sidebar.date_input('Data final',
                                           value=max_data,
                                           min_value=min_data,
                                           max_value=max_data)

        df_compras = df_compras[(df_compras['DiaCompra'] >= pd.Timestamp(data_inicial)) &
                                 (df_compras['DiaCompra'] <= pd.Timestamp(data_final))]

        dia_atual = df_compras['DiaCompra'].max()
        st.write('Dia máximo na base de dados: ', dia_atual)

        df_recencia = df_compras.groupby(by='ID_cliente', as_index=False)['DiaCompra'].max()
        df_recencia.columns = ['ID_cliente', 'DiaUltimaCompra']
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual - x).days)
        df_recencia.drop('DiaUltimaCompra', axis=1, inplace=True)

        st.write('## Frequência (F)')
        df_frequencia = df_compras[['ID_cliente', 'CodigoCompra']].groupby('ID_cliente').count().reset_index()
        df_frequencia.columns = ['ID_cliente', 'Frequencia']

        st.write('## Valor (V)')
        df_valor = df_compras[['ID_cliente', 'ValorTotal']].groupby('ID_cliente').sum().reset_index()
        df_valor.columns = ['ID_cliente', 'Valor']

        st.write('## Tabela RFV final')
        df_RF = df_recencia.merge(df_frequencia, on='ID_cliente')
        df_RFV = df_RF.merge(df_valor, on='ID_cliente')
        df_RFV.set_index('ID_cliente', inplace=True)
        st.write(df_RFV.head())

        kmeans = KMeans(n_clusters=4, random_state=42)
        df_RFV_scaled = (df_RFV - df_RFV.mean()) / df_RFV.std()
        df_RFV['Cluster'] = kmeans.fit_predict(df_RFV_scaled)

        marketing_actions = {
            'AAA': 'Enviar cupons de desconto, pedir para indicar nosso produto a um amigo, enviar amostras grátis ao lançar novos produtos.',
            'DDD': 'Clientes que gastaram pouco e fizeram poucas compras (Churn), nenhuma ação necessária.',
            'DDC': 'Enviar um e-mail com uma oferta introdutória para incentivar uma nova compra.',
            'BBB': 'Oferecer cupons personalizados e recompensas para aumentar a fidelidade.',
            'CDD': 'Enviar um lembrete com desconto em itens que compraram anteriormente.',
            'BAA': 'Enviar agradecimento com cupons de desconto em produtos relacionados.',
            'ABB': 'Oferecer promoções baseadas em produtos que compraram frequentemente.',
            'CDC': 'Enviar uma campanha de e-mail com promoções sazonais ou descontos limitados.',
            'BDD': 'Enviar um lembrete de carrinho abandonado com desconto.',
            'CBB': 'Oferecer recompensas para aumentar a frequência de compra.',
            'CBA': 'Enviar uma oferta de pacote para aumentar o valor do ticket médio.',
            'ABA': 'Oferecer recompensas VIP para manter a fidelidade.',
            'DCC': 'Enviar um e-mail de recuperação com desconto em produtos populares.',
            'BDC': 'Enviar uma campanha com frete grátis em novas compras.',
            'CCB': 'Oferecer descontos em itens similares aos mais comprados.',
            'BBA': 'Enviar campanhas de fidelidade e incentivos para compras regulares.',
            'BCC': 'Oferecer descontos progressivos baseados no volume de compras.',
            'CCC': 'Enviar e-mail com recomendações personalizadas para incentivar mais compras.',
            'ACC': 'Oferecer recompensas para compras mais frequentes.',
            'BCB': 'Enviar uma campanha de marketing com base nos produtos comprados.',
            'CAA': 'Enviar cupons de desconto para tentar recuperar.',
            'CBC': 'Enviar campanhas sazonais com produtos em oferta.',
            'DCB': 'Enviar lembrete com desconto para compras de alto valor.',
            'DCD': 'Enviar uma promoção de "primeira compra" com desconto.',
            'ADD': 'Enviar um agradecimento com oferta especial para reativar.',
            'BBC': 'Oferecer recompensas VIP para fortalecer a fidelidade.',
            'AAB': 'Enviar convites para eventos exclusivos ou acesso antecipado a novos produtos.',
            'ACB': 'Oferecer descontos personalizados com base em compras anteriores.',
            'CDB': 'Enviar uma campanha de e-mail com descontos em produtos populares.',
            'BCD': 'Enviar cupons para compras em categorias de interesse.',
            'ABC': 'Oferecer descontos progressivos para incentivar maior frequência.',
            'DBB': 'Enviar uma oferta para reativar com desconto.',
            'DBC': 'Oferecer promoções com base em produtos de interesse.',
            'DDB': 'Enviar uma campanha com desconto de "volte a comprar".',
            'CCD': 'Enviar recomendações de produtos em promoção.',
            'BAB': 'Enviar agradecimento com cupons de desconto.',
            'ADC': 'Enviar ofertas personalizadas para recompensar clientes recentes.',
            'ACD': 'Oferecer promoções sazonais para estimular novas compras.',
            'CAB': 'Enviar e-mail de fidelização com cupons de alto valor.',
            'BDB': 'Enviar lembretes com promoções limitadas no tempo.',
            'DAA': 'Enviar cupons de desconto para tentar recuperar.',
            'DBA': 'Enviar campanha de reativação com foco em itens mais vendidos.',
            'BCA': 'Oferecer descontos em pacotes de produtos.',
            'CCA': 'Oferecer recompensas por indicação de novos clientes.',
            'CBD': 'Enviar uma promoção para recompensar compras recentes.',
            'DBD': 'Enviar uma campanha de reativação com frete grátis.',
            'ABD': 'Enviar cupons de agradecimento para estimular a fidelidade.',
            'DCA': 'Enviar promoções sazonais com descontos significativos.',
            'CDA': 'Enviar uma oferta para compras recorrentes.',
            'BBD': 'Enviar campanhas de fidelidade para melhorar a relação.',
            'DDA': 'Enviar um e-mail de recuperação com promoções exclusivas.',
            'ADB': 'Enviar ofertas personalizadas com base no histórico de compras.',
            'DAB': 'Enviar promoções com itens de maior interesse.',
            'AAC': 'Enviar convites para eventos especiais e descontos VIP.',
            'ACA': 'Enviar cupons personalizados para recompensar compras frequentes.',
            'BDA': 'Enviar uma oferta de reativação com itens relacionados.',
            'CAC': 'Enviar uma campanha com promoções exclusivas.',
            'AAD': 'Oferecer recompensas para compras futuras.'
        }

        df_RFV['RFV_score'] = df_RFV['Cluster'].map(lambda x: 'AAA' if x == 0 else ('BBB' if x == 1 else ('CCC' if x == 2 else 'DDD')))
        df_RFV['Ações de marketing'] = df_RFV['RFV_score'].map(marketing_actions)

        st.write('Tabela final com ações de marketing')
        st.write(df_RFV.head())

        df_xlsx = to_excel(df_RFV)
        st.download_button(label='📥 Download',
                            data=df_xlsx,
                            file_name='RFV_Acoes_Marketing.xlsx')

if __name__ == '__main__':
    main()