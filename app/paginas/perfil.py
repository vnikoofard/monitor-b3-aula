"""Perfil do usuário: nome e foto (bucket 'avatares' do Supabase Storage)."""

import time

import streamlit as st

from conexao import cliente, consultar, perfil, usuario

TIPOS = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
LIMITE = 2 * 1024 * 1024        # 2 MB, o mesmo limite configurado no bucket

st.title("Meu perfil")
dados = perfil()
uid = usuario().id

esquerda, direita = st.columns([1, 2])
with esquerda:
    if dados.get("avatar_url"):
        st.image(dados["avatar_url"], width=160)
    else:
        st.info("Sem foto ainda.")

with direita:
    with st.form("nome"):
        nome = st.text_input("Nome", value=dados.get("nome") or "")
        if st.form_submit_button("Salvar nome"):
            consultar(cliente().table("profiles").update({"nome": nome}).eq("id", uid))
            st.rerun()

    arquivo = st.file_uploader("Trocar foto (PNG, JPEG ou WEBP, até 2 MB)", type=list(TIPOS))
    if arquivo and st.button("Enviar foto", type="primary"):
        conteudo = arquivo.getvalue()
        if len(conteudo) > LIMITE:
            st.error("A foto passa de 2 MB.")
        else:
            caminho = f"{uid}/avatar"           # a política do Storage exige a pasta = id do usuário
            tipo = TIPOS[arquivo.name.rsplit(".", 1)[-1].lower()]
            try:
                bucket = cliente().storage.from_("avatares")
                bucket.upload(path=caminho, file=conteudo,
                              file_options={"content-type": tipo, "upsert": "true"})
                # ?v=... evita que o navegador mostre a foto antiga guardada em cache
                url = f"{bucket.get_public_url(caminho)}?v={int(time.time())}"
                consultar(cliente().table("profiles").update({"avatar_url": url}).eq("id", uid))
                st.success("Foto atualizada.")
                st.rerun()
            except Exception as erro:  # noqa: BLE001
                st.error(f"Não foi possível enviar a foto: {erro}")
