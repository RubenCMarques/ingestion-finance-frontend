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


with SessionLocal() as db:
    if db.query(MovementType).count() == 0:
        db.add_all([
            MovementType(name="Expense"),
            MovementType(name="Income"),
        ])
        db.commit()

# Adding the options
def seed_lookups():
    with SessionLocal() as db:
        if not db.query(MovementType).first():
            db.add_all([
                MovementType(name="Expense"),
                MovementType(name="Income"),
            ])

        if not db.query(Category).first():
            db.add_all([
                Category(name="Restaurant"),
                Category(name="Rent"),
                Category(name="Transport"),
                Category(name="Salary"),
                Category(name="Given"),
                Category(name="Monthly Subscription"),
                Category(name="Travel"),
                Category(name="Supermarket"),
                Category(name="Health"),
                Category(name="Entertainment"),
                Category(name="Education"),
                Category(name="Gift"),
                Category(name="Hobbies"),
                Category(name="Other"),                
            ])

        if not db.query(PaymentMethod).first():
            db.add_all([
                PaymentMethod(name="Card"),
                PaymentMethod(name="Cash"),
                PaymentMethod(name="Transfer"),
                PaymentMethod(name="Revolut"),
                PaymentMethod(name="MBWay"),
            ])

        if not db.query(ProductType).first():
            db.add_all([
                ProductType(name="ETF"),
                ProductType(name="Stock"),
                ProductType(name="Crypto"),
                ProductType(name="Bond"),
                ProductType(name="CFD"),
                ProductType(name="Other"),
            ])

        db.commit()



seed_lookups()



# Base config
st.set_page_config(
    page_title="Despesas / Investimentos",
    page_icon="💸",
    layout="centered",
)


def main_app():
    st.title("Ingestion App Finance")

    # Load lookup tables
    with SessionLocal() as db:
        movement_type_map = {mt.name: mt.id for mt in db.query(MovementType).all()}
        category_map = {c.name: c.id for c in db.query(Category).all()}
        payment_method_map = {pm.name: pm.id for pm in db.query(PaymentMethod).all()}
        product_type_map = {pt.name: pt.id for pt in db.query(ProductType).all()}

    transaction_type_choices = list(movement_type_map.keys())
    category_choices = list(category_map.keys())
    payment_method_choices = list(payment_method_map.keys())
    product_type_choices = list(product_type_map.keys())

    type_ = st.selectbox("Tipo", transaction_type_choices + ["Investment"])

    # ---------------- EXPENSE / INCOME ----------------
    if type_ in transaction_type_choices:
        amount = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        currency = st.selectbox("Moeda", ["EUR", "USD", "GBP", "JPY", "CHF"])

        category_name = (
            st.selectbox("Categoria", category_choices)
            if category_choices
            else None
        )

        selected_date = st.date_input(
            "Data",
            value=st.session_state.get("selected_date", date.today()),
            key="selected_date",
        )

        store = st.text_input("Loja", value=st.session_state.get("store", ""), key="store")

        payment_method_name = st.selectbox(
            "Método de Pagamento",
            [""] + payment_method_choices if payment_method_choices else [""],
        )

        source = st.text_input("Fonte (opcional)")
        notes = st.text_area("Notas (opcional)")

    # ---------------- INVESTMENT ----------------
    else:
        st.subheader("Detalhes do Investimento")

        ticker = st.text_input("Ticker / Nome do Ativo (ex: AAPL, VWCE, BTC)")

        product_type_name = (
            st.selectbox("Tipo de Produto", product_type_choices)
            if product_type_choices
            else None
        )

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

    # ---------------- SAVE ----------------
    if st.button("Guardar"):
        db: Session = SessionLocal()

        try:
            if type_ in transaction_type_choices:
                if amount <= 0:
                    st.error("O valor tem de ser maior que zero.")
                elif not category_name:
                    st.error("Tens de escolher uma categoria.")
                else:
                    tx = Transaction(
                        movement_type_id=movement_type_map[type_],
                        amount=amount,
                        currency=currency,
                        category_id=category_map[category_name],
                        payment_method_id=payment_method_map.get(payment_method_name),
                        transaction_date=selected_date,
                        source=store or None,
                        notes=notes or None,
                    )

                    db.add(tx)
                    db.commit()
                    st.success("Despesa/Receita guardada")

            else:
                if not ticker:
                    st.error("O ticker é obrigatório para investimentos.")
                elif unit_price <= 0 or quantity <= 0:
                    st.error("Preço e quantidade têm de ser maiores que zero.")
                elif not product_type_name:
                    st.error("Tens de escolher um tipo de produto.")
                else:
                    inv = Investment(
                        ticker=ticker,
                        product_type_id=product_type_map[product_type_name],
                        unit_price=unit_price,
                        quantity=quantity,
                        total_value=unit_price * quantity,
                        currency=currency,
                        investment_date=selected_date,
                        notes=notes or None,
                    )

                    db.add(inv)
                    db.commit()
                    st.success("Investimento guardado")

            # ---------- RESET FORM ----------
            for key in list(st.session_state.keys()):
                if key not in ("authentication_status", "username"):
                    del st.session_state[key]

            st.rerun()

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
