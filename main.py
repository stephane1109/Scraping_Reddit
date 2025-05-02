########
# Extraction posts and comments Reddit - en local
# wwww.codeandcortex.fr
########

# pip install streamlit praw
# python -m streamlit run main.py

import streamlit as st
import praw
from langdetect import detect, LangDetectException
from datetime import datetime
import time

# Détection de la langue
def est_en_francais(texte):
    try:
        return detect(texte) == 'fr'
    except LangDetectException:
        return False

# Conversion date -> timestamp
def date_to_timestamp(date_obj):
    return int(time.mktime(date_obj.timetuple()))

# Recherche Reddit
def rechercher_posts_depuis_date(mot_cle, client_id, client_secret, user_agent, date_debut_timestamp, filtre_titre_seulement=False):
    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         user_agent=user_agent)

    posts = reddit.subreddit("all").search(mot_cle, sort="new", limit=None)
    resultats = []
    total_commentaires = 0

    for post in posts:
        if post.created_utc < date_debut_timestamp:
            break

        if filtre_titre_seulement and mot_cle.lower() not in post.title.lower():
            continue

        contenu_post = f"{post.title} {post.selftext}" if not filtre_titre_seulement else post.title
        if est_en_francais(contenu_post):
            post_data = {
                'titre': post.title,
                'auteur': str(post.author),
                'score': post.score,
                'permalink': f"https://www.reddit.com{post.permalink}",
                'subreddit': post.subreddit.display_name,
                'corps': post.selftext,
                'date': datetime.utcfromtimestamp(post.created_utc),
                'commentaires': []
            }

            try:
                post.comments.replace_more(limit=0)
                for commentaire in post.comments.list():
                    if commentaire.body and est_en_francais(commentaire.body):
                        post_data['commentaires'].append({
                            'auteur': str(commentaire.author),
                            'texte': commentaire.body
                        })
                        total_commentaires += 1
            except Exception as e:
                post_data['commentaires'].append({
                    'auteur': 'erreur',
                    'texte': f"[Erreur de lecture des commentaires] : {e}"
                })

            resultats.append(post_data)

    return resultats, total_commentaires

# Génération du fichier texte complet
def generer_fichier_txt(resultats):
    contenu = ""
    for post in resultats:
        contenu += f"=== POST : {post['titre']} ===\n"
        contenu += f"Auteur : {post['auteur']} | Score : {post['score']} | Subreddit : {post['subreddit']}\n"
        contenu += f"Lien Reddit : {post['permalink']}\n"
        contenu += f"Date : {post['date']}\n\n"
        contenu += f"{post['corps']}\n\n"
        contenu += "--- Commentaires ---\n"
        for com in post['commentaires']:
            contenu += f"*{com['auteur']} : {com['texte']}\n"
        contenu += "\n===============================\n\n"
    return contenu

# Interface utilisateur Streamlit
st.title("Scraper Reddit : posts et commentaires en français")
st.markdown("www.codeandcortex.fr")

st.markdown("Identifiants API Reddit")
client_id = st.text_input("Client ID", type="password")
client_secret = st.text_input("Client Secret", type="password")
user_agent = st.text_input("User Agent", value="api_streamlit/1.0 (by u/Accurate-Command-285)") # a remplacer par le nom de votre api et le nom de votre compte

st.markdown("Paramètres de recherche")
mot_cle = st.text_input("Mot-clé à rechercher", value="Exemple : Trump")
date_debut = st.date_input("Date de début (UTC)", value=datetime(2024, 1, 1))
filtre_titre = st.checkbox("Rechercher uniquement dans le titre")

# Lancement de la recherche
if st.button("Lancer la recherche"):
    if not all([client_id, client_secret, user_agent, mot_cle]):
        st.warning("Merci de remplir tous les champs.")
    else:
        try:
            date_timestamp = date_to_timestamp(date_debut)
            with st.spinner("Recherche en cours..."):
                resultats, total_commentaires = rechercher_posts_depuis_date(
                    mot_cle, client_id, client_secret, user_agent, date_timestamp, filtre_titre
                )

            if resultats:
                st.session_state["resultats"] = resultats
                st.session_state["contenu_txt"] = generer_fichier_txt(resultats)
                st.session_state["total_commentaires"] = total_commentaires
                st.session_state["recherche_effectuee"] = True
            else:
                st.warning("Aucun post trouvé pour ce mot-clé et cette date.")
        except Exception as e:
            st.error(f"Erreur : {e}")

# Affichage des résultats après recherche
if st.session_state.get("recherche_effectuee"):
    resultats = st.session_state["resultats"]
    total_commentaires = st.session_state["total_commentaires"]

    st.subheader("Statistiques")
    st.markdown(f"Nombre de posts trouvés : **{len(resultats)}**")
    st.markdown(f"Nombre total de commentaires en français : **{total_commentaires}**")

    for i, post in enumerate(resultats[:2], start=1):
        st.markdown(f"### Post {i}")
        st.markdown(f"**{post['titre']}**")
        st.markdown(f"Auteur : {post['auteur']} | Score : {post['score']}")
        st.markdown(f"Subreddit : {post['subreddit']} | Date : {post['date']}")
        st.markdown(f"[Lien vers le post Reddit]({post['permalink']})")

        extrait = post['corps'][:500] + ("..." if len(post['corps']) > 500 else "")
        if extrait:
            st.markdown(f"Extrait : {extrait}")

        st.markdown("5 premiers commentaires en français :")
        for com in post['commentaires'][:5]:
            st.markdown(f"*{com['auteur']}* : {com['texte']}")

    st.download_button(
        label="Télécharger tous les résultats (.txt)",
        data=st.session_state["contenu_txt"],
        file_name="reddit_resultats.txt",
        mime="text/plain"
    )
