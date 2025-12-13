import os
from datetime import date
from string import Template

import streamlit as st
from sqlalchemy.orm import Session
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

from app.database import SessionLocal, Base, engine
from app.models import (
    Transaction,
    Investment,
    MovementType,
    Category,
    PaymentMethod,
    ProductType,
)

# Criar tabelas (transactions + investments) se ainda não existirem
Base.metadata.create_all(bind=engine)

# Base config
st.set_page_config(
    page_title="Despesas / Investimentos",
    page_icon="💸",
    layout="centered",
)


def main_app():
    st.title("Ingestion App Finance")

    # Carregar listas das tabelas de lookup
    with SessionLocal() as db:
        movement_type_map = {mt.name: mt.id for mt in db.query(MovementType).all()}
        category_map = {c.name: c.id for c in db.query(Category).all()}
        payment_method_map = {pm.name: pm.id for pm in db.query(PaymentMethod).all()}
        product_type_map = {pt.name: pt.id for pt in db.query(ProductType).all()}

    transaction_type_choices = list(movement_type_map.keys())
    category_choices = list(category_map.keys())
    payment_method_choices = list(payment_method_map.keys())
    product_type_choices = list(product_type_map.keys())

    # Tipo de registo (decide qual dos formulários deve aparecer)
    type_ = st.selectbox("Tipo", transaction_type_choices + ["Investment"])

    # Expense/Income settings
    if type_ in transaction_type_choices:
        amount = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        currency = st.selectbox(
            "Moeda",
            ["EUR", "USD", "GBP", "JPY", "CHF"],
        )

        if category_choices:
            category_name = st.selectbox("Categoria", category_choices)
        else:
            category_name = None
            st.warning("Ainda não existem categorias na base de dados.")

        selected_date = st.date_input(
            "Data",
            value=st.session_state.get("selected_date", date.today()),
            key="selected_date",
        )
        st.text_input(
            "Loja", value=st.session_state.get("store", ""), key="store"
        )

        payment_method_name = st.selectbox(
            "Método de Pagamento",
            [""] + payment_method_choices if payment_method_choices else [""],
        )

        source = st.text_input("Fonte (opcional)")
        notes = st.text_area("Notas (opcional)")

    # Investmennt settings
    elif type_ == "Investment":
        st.subheader("Detalhes do Investimento")

        ticker = st.text_input("Ticker / Nome do Ativo (ex: AAPL, VWCE, BTC)")

        if product_type_choices:
            product_type_name = st.selectbox("Tipo de Produto", product_type_choices)
        else:
            product_type_name = None
            st.warning("Ainda não existem tipos de produto na base de dados.")

        unit_price = st.number_input(
            "Preço por unidade (€)", min_value=0.0, step=0.01, format="%.2f"
        )

        selected_date = st.date_input(
            "Data",
            value=st.session_state.get("selected_date", date.today()),
            key="selected_date",
        )

        quantity = st.number_input(
            "Quantidade comprada", min_value=0.0, step=0.01, format="%.4f"
        )
        currency = st.selectbox("Moeda", ["EUR", "USD", "GBP", "JPY", "CHF"])
        notes = st.text_area("Notas (opcional)")

    # Save
    if st.button("Guardar"):
        db: Session = SessionLocal()

        try:
            if type_ in transaction_type_choices:
                if amount <= 0:
                    st.error("O valor tem de ser maior que zero.")
                elif not category_name:
                    st.error("Tens de escolher uma categoria.")
                else:
                    movement_type_id = movement_type_map[type_]
                    category_id = category_map.get(category_name)
                    payment_method_id = (
                        payment_method_map.get(payment_method_name)
                        if payment_method_name
                        else None
                    )

                    tx = Transaction(
                        movement_type_id=movement_type_id,
                        amount=amount,
                        currency=currency,
                        category_id=category_id,
                        payment_method_id=payment_method_id,
                        source=source or None,
                        notes=notes or None,
                    )
                    db.add(tx)
                    db.commit()
                    st.success("Despesa/Receita guardada")

            elif type_ == "Investment":
                if not ticker:
                    st.error("O ticker é obrigatório para investimentos.")
                elif unit_price <= 0 or quantity <= 0:
                    st.error("Preço e quantidade têm de ser maiores que zero.")
                elif not product_type_name:
                    st.error("Tens de escolher um tipo de produto.")
                else:
                    total_value = unit_price * quantity
                    product_type_id = product_type_map[product_type_name]

                    inv = Investment(
                        ticker=ticker,
                        product_type_id=product_type_id,
                        unit_price=unit_price,
                        quantity=quantity,
                        total_value=total_value,
                        currency=currency,
                        notes=notes or None,
                    )
                    db.add(inv)
                    db.commit()
                    st.success("Investimento guardado")

        except Exception as e:
            db.rollback()
            st.error(f"Erro ao guardar: {e}")
        finally:
            db.close()


# AUTENTICAÇÃO

# Lê config_auth.yaml da root do projeto (no container está em /code/config_auth.yaml)
CONFIG_PATH = "config_auth.yaml"

with open(CONFIG_PATH, "r") as f:
    raw_yaml = f.read()

# Substitui ${VAR} no yaml por variáveis de ambiente (HASHED_PASSWORD, COOKIE_KEY, etc.)
raw_yaml = Template(raw_yaml).substitute(os.environ)

config = yaml.load(raw_yaml, Loader=SafeLoader)
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

authenticator.login("main")

authentication_status = st.session_state.get("authentication_status")

if authentication_status:
    authenticator.logout("Logout", "sidebar")
    main_app()

elif authentication_status is False:
    st.error("Username/password incorretos.")

else:
    st.warning("Por favor, introduz o teu username e password.")
