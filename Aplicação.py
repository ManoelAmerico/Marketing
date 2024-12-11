import numpy as np
import pandas as pd
import streamlit as st


from datetime import datetime
from PIL import Image
from io import BytesIO

st.set_page_config(page_title = 'RFV', \
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
    """Classifica como melhor o menor quartil 
       x = valor da linha,
       r = recencia,
       q_dict = quartil dicionario   
    """
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
    """Classifica como melhor o maior quartil 
       x = valor da linha,
       fv = frequencia ou valor,
       q_dict = quartil dicionario   
    """
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
    data_file_1 = st.sidebar.file_uploader("Bank marketing data", type = ['csv', 'xlsx'])

    if (data_file_1 is not None):
        df_compras = pd.read_csv(data_file_1, infer_datetime_format=True, parse_dates=['DiaCompra'])

        st.write('## Recência(R)')
        
        min_data = df_compras['DiaCompra'].min()
        max_data = df_compras['DiaCompra'].max()

        data_inicial = st.sidebar.date_input('Data inicial',
                                     value = min_data,
                                     min_value = min_data,
                                     max_value = max_data)
        data_final = st.sidebar.date_input('Data final',
                                   value = min_data,
                                   min_value = min_data,
                                   max_value = max_data)
        
        dia_atual = df_compras['DiaCompra'].max()
        st.write('Dia máximo na base de dados: ', dia_atual)

        st.write('Quantos dias faz que o cliente fez a sua última compra?')

        df_recencia = df_compras.groupby(by='ID_cliente', as_index=False)['DiaCompra'].max()
        df_recencia.columns = ['ID_cliente', 'DiaUltimaCompra']
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual - x).days)
        st.write(df_recencia.head())

        df_recencia.drop('DiaUltimaCompra', axis=1, inplace=True)

        st.write('## Frequência (F)')
        st.write('Quantas vezes cada cliente comprou com a gente?')
        df_frequencia = df_compras[['ID_cliente', 'CodigoCompra']].groupby('ID_cliente').count().reset_index()
        df_frequencia.columns = ['ID_cliente', 'Frequencia']
        st.write(df_frequencia.head())

        st.write('## Valor (V)')
        st.write('Quanto cada cliente gastou no periodo?')
        df_valor = df_compras[['ID_cliente', 'ValorTotal']].groupby('ID_cliente').sum().reset_index()
        df_valor.columns = ['ID_cliente', 'Valor']
        st.write(df_valor.head())

        st.write('## Tabela RFV final')
        df_RF = df_recencia.merge(df_frequencia, on='ID_cliente')
        df_RFV = df_RF.merge(df_valor, on='ID_cliente')
        df_RFV.set_index('ID_cliente', inplace=True)
        st.write(df_RFV.head())

        st.write('## Segmentação utilizando o RFV')
        st.write("Um jeito de segmentar os clientes é criando quartis para cada componente do RFV, sendo que o melhor quartil é chamado de 'A', o segundo melhor quartil de 'B', o terceiro melhor de 'C' e o pior de 'D'. O melhor e o pior depende da componente. Po exemplo, quanto menor a recência melhor é o cliente (pois ele comprou com a gente tem pouco tempo) logo o menor quartil seria classificado como 'A', já pra componente frêquencia a lógica se inverte, ou seja, quanto maior a frêquencia do cliente comprar com a gente, melhor ele/a é, logo, o maior quartil recebe a letra 'A'.")
        st.write('Se a gente tiver interessado em mais ou menos classes, basta a gente aumentar ou diminuir o número de quantils pra cada componente.')

        st.write('Quartis para o RFV')
        quartis = df_RFV.quantile(q=[0.25,0.5,0.75])
        st.write(quartis)

        st.write('Tabela após a criação dos grupos')
        df_RFV['R_quartil'] = df_RFV['Recencia'].apply(recencia_class,
                                                       args=('Recencia', quartis))
        df_RFV['F_quartil'] = df_RFV['Frequencia'].apply(freq_val_class,
                                                         args=('Frequencia', quartis))
        df_RFV['V_quartil'] = df_RFV['Valor'].apply(freq_val_class,
                                                    args=('Valor', quartis))
        df_RFV['RFV_score'] = (df_RFV.R_quartil
                               + df_RFV.F_quartil
                               + df_RFV.V_quartil)
        st.write(df_RFV.head())

        st.write('Quantidade de clientes por grupos')
        st.write(df_RFV['RFV_score'].value_counts())

        st.write('#### Clientes com menor recência, maior frequência e maior valor gasto')
        st.write(df_RFV[df_RFV['RFV_score']=='AAA'].sort_values('Valor', ascending=False).head(10))

        st.write('### Açòes de marketing/CRM')

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

        df_RFV['acoes de marketing/crm'] = df_RFV['RFV_score'].map(marketing_actions)
        st.write(df_RFV.head())

        df_xlsx = to_excel(df_RFV)
        st.download_button(label='📥 Download',
                            data=df_xlsx ,
                            file_name= 'RFV_.xlsx')
        
        st.write('Quantidade de clientes por tipo de ações')
        st.write(df_RFV['acoes de marketing/crm'].value_counts(dropna=False))


if __name__ == '__main__':
    main()