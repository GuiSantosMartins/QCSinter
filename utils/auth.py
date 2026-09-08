import hashlib
import hmac
import json
import os
from pathlib import Path

import streamlit as st

AUTH_SESSION_KEY = "authenticated_user"
HASH_ALGORITHM = "pbkdf2_sha256"
HASH_ITERATIONS = 260000
PROJECT_ROOT = Path(__file__).resolve().parents[1]
USER_STORE_PATH = PROJECT_ROOT / ".streamlit" / "users.json"


def require_login(page_name):
    if st.session_state.get(AUTH_SESSION_KEY):
        _show_logged_in_user()
        return

    st.title("Acesso Restrito")
    st.caption(page_name)

    users = _load_users()
    if not users:
        _render_first_user_form()
        st.stop()

    login_tab, new_user_tab, password_tab = st.tabs(
        ["Entrar", "Novo usuário", "Alterar senha"]
    )

    with login_tab:
        _render_login_form(users)

    with new_user_tab:
        _render_new_user_form(users)

    with password_tab:
        _render_change_password_form(users)

    st.stop()


def _show_logged_in_user():
    username = st.session_state[AUTH_SESSION_KEY]
    with st.sidebar:
        st.caption(f"Usuário: {username}")

        with st.expander("Alterar senha"):
            _render_change_password_form(_load_users(), fixed_username=username)

        if st.button("Sair"):
            del st.session_state[AUTH_SESSION_KEY]
            _rerun()


def _render_login_form(users):
    with st.form("login_form"):
        username = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        username = username.strip()
        if _valid_credentials(users, username, password):
            st.session_state[AUTH_SESSION_KEY] = username
            _rerun()

        st.error("Usuário ou senha inválidos.")


def _render_first_user_form():
    st.info("Nenhum usuário configurado. Crie o primeiro usuário para liberar o dashboard.")

    with st.form("first_user_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        confirm = st.text_input("Confirmar senha", type="password")
        submitted = st.form_submit_button("Criar usuário")

    if submitted:
        success, message = _create_user(username, password, confirm)
        if success:
            st.success("Usuário criado. Faça login para continuar.")
            _rerun()
        else:
            st.error(message)


def _render_new_user_form(users):
    registration_code = "cnq1961"
    #if not registration_code:
        #st.info(
            #"Cadastro de novos usuários bloqueado. Configure "
            #"`auth.registration_code` em `.streamlit/secrets.toml`."
        #)
        #return

    with st.form("new_user_form"):
        code = st.text_input("Código de cadastro", type="password")
        username = st.text_input("Novo usuário")
        password = st.text_input("Senha", type="password")
        confirm = st.text_input("Confirmar senha", type="password")
        submitted = st.form_submit_button("Criar usuário")

    if submitted:
        if not hmac.compare_digest(code, registration_code):
            st.error("Código de cadastro inválido.")
            return

        success, message = _create_user(username, password, confirm, users)
        if success:
            st.success("Usuário criado. Ele já pode fazer login.")
        else:
            st.error(message)


def _render_change_password_form(users, fixed_username=None):
    form_key = "change_password_form"
    if fixed_username:
        form_key = f"{form_key}_{fixed_username}"

    with st.form(form_key):
        if fixed_username:
            username = fixed_username
            st.text_input("Usuário", value=fixed_username, disabled=True)
        else:
            username = st.text_input("Usuário", key=f"{form_key}_user")

        current = st.text_input("Senha atual", type="password", key=f"{form_key}_current")
        new_password = st.text_input("Nova senha", type="password", key=f"{form_key}_new")
        confirm = st.text_input("Confirmar nova senha", type="password", key=f"{form_key}_confirm")
        submitted = st.form_submit_button("Alterar senha")

    if submitted:
        username = username.strip()
        if not _valid_credentials(users, username, current):
            st.error("Usuário ou senha atual inválidos.")
            return

        success, message = _set_password(username, new_password, confirm, users)
        if success:
            st.success("Senha alterada.")
        else:
            st.error(message)


def _create_user(username, password, confirm, users=None):
    username = username.strip()
    users = users or _load_users()

    valid, message = _validate_user_input(username, password, confirm)
    if not valid:
        return False, message

    if username in users:
        return False, "Usuário já existe."

    file_users = _load_file_users()
    file_users[username] = _hash_password(password)
    _save_file_users(file_users)
    return True, "Usuário criado."


def _set_password(username, password, confirm, users=None):
    users = users or _load_users()

    valid, message = _validate_user_input(username, password, confirm)
    if not valid:
        return False, message

    if username not in users:
        return False, "Usuário não encontrado."

    file_users = _load_file_users()
    file_users[username] = _hash_password(password)
    _save_file_users(file_users)
    return True, "Senha alterada."


def _validate_user_input(username, password, confirm):
    if not username:
        return False, "Informe o usuário."
    if len(username) < 3:
        return False, "Usuário deve ter pelo menos 3 caracteres."
    if not username.replace("_", "").replace(".", "").replace("-", "").isalnum():
        return False, "Use apenas letras, números, ponto, hífen ou sublinhado no usuário."
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres."
    if password != confirm:
        return False, "As senhas não conferem."
    return True, ""


def _load_users():
    users = {}
    users.update(_load_secret_users())
    users.update(_load_file_users())
    return users


def _load_secret_users():
    try:
        auth_config = st.secrets.get("auth", {})
        return dict(auth_config.get("users", {}))
    except Exception:
        return {}


def _load_file_users():
    if not USER_STORE_PATH.exists():
        return {}

    try:
        with USER_STORE_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}

    users = data.get("users", {})
    return users if isinstance(users, dict) else {}


def _save_file_users(users):
    USER_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"users": dict(sorted(users.items()))}
    with USER_STORE_PATH.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def _get_registration_code():
    try:
        return str(st.secrets.get("auth", {}).get("registration_code", "")).strip()
    except Exception:
        return ""


def _valid_credentials(users, username, password):
    if not username or username not in users:
        return False

    expected = str(users[username])

    if expected.startswith(f"{HASH_ALGORITHM}$"):
        return _verify_pbkdf2_password(password, expected)

    if expected.startswith("sha256:"):
        received = "sha256:" + hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(received, expected)

    return hmac.compare_digest(password, expected)


def _hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS,
    )
    return (
        f"{HASH_ALGORITHM}${HASH_ITERATIONS}$"
        f"{salt.hex()}${digest.hex()}"
    )


def _verify_pbkdf2_password(password, stored_value):
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_value.split("$", 3)
        if algorithm != HASH_ALGORITHM:
            return False

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
    except (TypeError, ValueError):
        return False

    return hmac.compare_digest(digest.hex(), digest_hex)


def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()
