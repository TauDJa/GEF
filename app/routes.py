# app/routes.py

# --- Imports Essentiels ---
import os
import subprocess
import traceback
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.orm import joinedload
from datetime import datetime # Assurez-vous d'avoir cet import

# --- Import de vos Modèles ---
from .models import db, Gef, Personnel, Wilaya, Commune, Telephone, TypeEquipement, Agrement, GefEquipement, GefAgrement

# --- Création du Blueprint ---
main_bp = Blueprint('main', __name__)


# === Route 1 : Le Tableau de Bord Principal ===
@main_bp.route('/')
def dashboard():
    # (Le code du dashboard reste inchangé)
    gef_count, personnel_count, wilaya_count = "N/A", "N/A", "N/A"
    try:
        database_url = os.environ.get('DATABASE_URL', '')
        # database_url = "postgresql://postgres:12345678@localhost:5432/ogef" 
        parsed = urlparse(database_url)
        env = os.environ.copy()
        if parsed.password: env['PGPASSWORD'] = parsed.password
        env['PGCLIENTENCODING'] = 'latin1'
        
        cmd_gef = ['psql', '-h', parsed.hostname or 'localhost', '-U', parsed.username or 'postgres', '-d', parsed.path[1:] if parsed.path else 'postgres', '-tAc', 'SELECT COUNT(*) FROM gef;']
        result_gef = subprocess.run(cmd_gef, capture_output=True, text=True, env=env, timeout=5)
        if result_gef.returncode == 0 and result_gef.stdout.strip().isdigit(): gef_count = result_gef.stdout.strip()

        cmd_personnel = ['psql', '-h', parsed.hostname or 'localhost', '-U', parsed.username or 'postgres', '-d', parsed.path[1:] if parsed.path else 'postgres', '-tAc', 'SELECT COUNT(*) FROM personnel;']
        result_personnel = subprocess.run(cmd_personnel, capture_output=True, text=True, env=env, timeout=5)
        if result_personnel.returncode == 0 and result_personnel.stdout.strip().isdigit(): personnel_count = result_personnel.stdout.strip()

        cmd_wilaya = ['psql', '-h', parsed.hostname or 'localhost', '-U', parsed.username or 'postgres', '-d', parsed.path[1:] if parsed.path else 'postgres', '-tAc', 'SELECT COUNT(DISTINCT c.code_wilaya) FROM commune c JOIN gef g ON c.code_commu = g.commune_c;']
        result_wilaya = subprocess.run(cmd_wilaya, capture_output=True, text=True, env=env, timeout=5)
        if result_wilaya.returncode == 0 and result_wilaya.stdout.strip().isdigit(): wilaya_count = result_wilaya.stdout.strip()

    except Exception as e:
        print(f"Erreur lors du comptage pour le dashboard : {e}")
        flash("Impossible de charger les statistiques du dashboard.", "warning")

    return render_template('dashboard.html', gef_count=gef_count, personnel_count=personnel_count, wilaya_count=wilaya_count)


# === Route 2 : Le Formulaire pour Ajouter un GEF ===
@main_bp.route('/gef/add', methods=['GET', 'POST'])
def add_gef():
    # --- LOGIQUE POST ---
    if request.method == 'POST':
        try:
            gef_numero = request.form.get('numero')
            existing_gef = Gef.query.filter_by(numero=gef_numero).first()
            if existing_gef:
                flash(f"Erreur : Le GEF avec le numéro {gef_numero} existe déjà.", 'danger')
                return redirect(url_for('main.add_gef'))

            date_str = request.form.get('date_obt')
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
            date_naissance_str = request.form.get('date_naiss')
            date_naissance_obj = datetime.strptime(date_naissance_str, '%Y-%m-%d').date() if date_naissance_str else None

            new_gef = Gef(
                numero=gef_numero,
                date_obt=date_obj, 
                n_p=request.form.get('n_p'),
                date_naiss=date_naissance_obj,
                nim=request.form.get('nim') or None,
                nif=request.form.get('nif') or None,
                email=request.form.get('email'),
                adresse=request.form.get('adresse'),
                commune_c=request.form.get('commune_c'),
                statut_bureau=request.form.get('statut_bureau'),
                situation=request.form.get('situation'),
                observations=request.form.get('observations') # ✅ Ajout
            )
            db.session.add(new_gef)
            
            # --- Ajout des éléments liés ---
            # (le code pour personnel, telephones, etc. reste inchangé)
            for nom, prenom, profile in zip(request.form.getlist('personnel_nom'), request.form.getlist('personnel_prenom'), request.form.getlist('personnel_profile')):
                 db.session.add(Personnel(nom=nom, prenom=prenom, profile=profile, n_gef=gef_numero))
            for type_tel, num in zip(request.form.getlist('telephone_type'), request.form.getlist('telephone_numero')):
                 db.session.add(Telephone(type_tel=type_tel, num=num, n_gef=gef_numero))
            for id_type, quantite in zip(request.form.getlist('equipement_id'), request.form.getlist('equipement_quantite')):
                 db.session.add(GefEquipement(n_gef=gef_numero, id_type=id_type, quantite=quantite))
            for agrement_id in request.form.getlist('agrement_ids'):
                 db.session.add(GefAgrement(gef_n=gef_numero, agrement_id=agrement_id)) 

            db.session.commit()
            flash('GEF ajouté avec succès !', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            # (gestion d'erreur inchangée)
            print("---! ERREUR LORS DE L'ENREGISTREMENT DU GEF !---")
            traceback.print_exc()
            print("-------------------------------------------------")
            db.session.rollback()
            flash(f"Une erreur est survenue, le GEF n'a pas été enregistré. Détails: {e}", 'danger')
            return redirect(url_for('main.add_gef'))

    # --- LOGIQUE GET ---
    # (le code GET reste inchangé)
    wilayas, type_equipements, agrements = [], [], []
    try:
        wilayas = Wilaya.query.order_by(Wilaya.nom_wilaya).all()
        type_equipements = TypeEquipement.query.order_by(TypeEquipement.nom_type).all()
        agrements = Agrement.query.order_by(Agrement.nom).all()
    except Exception as e:
        flash(f"Erreur de base de données lors du chargement du formulaire : {e}", "danger")

    return render_template(
        'add_gef.html', 
        wilayas=wilayas, 
        type_equipements=type_equipements, 
        agrements=agrements
    )


# === Route 3 : Affichage du Formulaire de Modification ===
@main_bp.route('/gef/edit/<int:gef_numero>', methods=['GET'])
def edit_gef(gef_numero):
    # (le code GET pour edit reste inchangé)
    try:
        gef = Gef.query.filter_by(numero=gef_numero).options(joinedload(Gef.commune).joinedload(Commune.wilaya)).first_or_404()
        personnels = Personnel.query.filter_by(n_gef=gef_numero).all()
        telephones = Telephone.query.filter_by(n_gef=gef_numero).all()
        equipements_actuels = GefEquipement.query.filter_by(n_gef=gef_numero).all()
        ids_equipements_actuels = {eq.id_type: eq.quantite for eq in equipements_actuels}
        agrements_actuels = GefAgrement.query.filter_by(gef_n=gef_numero).all()
        ids_agrements_actuels = [ag.agrement_id for ag in agrements_actuels] 
        wilayas = Wilaya.query.order_by(Wilaya.nom_wilaya).all()
        communes = []
        if gef.commune:
            communes = Commune.query.filter_by(code_wilaya=gef.commune.code_wilaya).order_by(Commune.nom_commun).all()
        type_equipements = TypeEquipement.query.order_by(TypeEquipement.nom_type).all()
        agrements = Agrement.query.order_by(Agrement.nom).all()
        return render_template(
            'edit_gef.html', gef=gef, personnels=personnels, telephones=telephones,
            ids_equipements_actuels=ids_equipements_actuels, ids_agrements_actuels=ids_agrements_actuels,
            wilayas=wilayas, communes=communes, type_equipements=type_equipements, agrements=agrements
        )
    except Exception as e:
        flash(f"Erreur lors du chargement du formulaire de modification : {e}", 'danger')
        return redirect(url_for('main.dashboard'))


# === Route 4 : Sauvegarde des Modifications ===
@main_bp.route('/gef/update/<int:gef_numero>', methods=['POST'])
def update_gef(gef_numero):
    try:
        gef_to_update = Gef.query.filter_by(numero=gef_numero).first_or_404()

        # --- Mise à jour des dates ---
        date_str = request.form.get('date_obt')
        gef_to_update.date_obt = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        
        # ✅ LIGNES MANQUANTES AJOUTÉES ICI
        date_naissance_str = request.form.get('date_naiss')
        gef_to_update.date_naiss = datetime.strptime(date_naissance_str, '%Y-%m-%d').date() if date_naissance_str else None
        
        # --- Mise à jour des autres champs ---
        gef_to_update.n_p = request.form.get('n_p')
        gef_to_update.nim = request.form.get('nim') or None
        gef_to_update.nif = request.form.get('nif') or None
        gef_to_update.email = request.form.get('email')
        gef_to_update.adresse = request.form.get('adresse')
        gef_to_update.commune_c = request.form.get('commune_c')
        gef_to_update.statut_bureau = request.form.get('statut_bureau')
        gef_to_update.situation = request.form.get('situation')
        gef_to_update.observations = request.form.get('observations')
        gef_to_update.lieu_naiss_wc = request.form.get('lieu_naiss_wc') or None
        gef_to_update.lieu_naiss_cc = request.form.get('lieu_naiss_cc') or None
        
        # --- Stratégie "Effacer et Recréer" ---
        Personnel.query.filter_by(n_gef=gef_numero).delete()
        for nom, prenom, profile in zip(request.form.getlist('personnel_nom'), request.form.getlist('personnel_prenom'), request.form.getlist('personnel_profile')):
             db.session.add(Personnel(nom=nom, prenom=prenom, profile=profile, n_gef=gef_numero))
        
        Telephone.query.filter_by(n_gef=gef_numero).delete()
        for type_tel, num in zip(request.form.getlist('telephone_type'), request.form.getlist('telephone_numero')):
             db.session.add(Telephone(type_tel=type_tel, num=num, n_gef=gef_numero))

        GefEquipement.query.filter_by(n_gef=gef_numero).delete()
        for id_type, quantite in zip(request.form.getlist('equipement_id'), request.form.getlist('equipement_quantite')):
             db.session.add(GefEquipement(n_gef=gef_numero, id_type=id_type, quantite=quantite))

        GefAgrement.query.filter_by(gef_n=gef_numero).delete()
        for agrement_id in request.form.getlist('agrement_ids'):
             db.session.add(GefAgrement(gef_n=gef_numero, agrement_id=agrement_id))
            
        db.session.commit()
        flash(f"Le GEF N°{gef_numero} a été mis à jour avec succès.", 'success')

    except Exception as e:
        print("---! ERREUR LORS DE LA MISE À JOUR DU GEF !---")
        traceback.print_exc()
        print("---------------------------------------------")
        db.session.rollback()
        flash(f"Une erreur est survenue lors de la mise à jour : {e}", 'danger')

    return redirect(url_for('main.dashboard'))


# === Route 5 : Suppression d'un GEF ===
@main_bp.route('/gef/delete/<int:gef_numero>', methods=['POST'])
def delete_gef(gef_numero):
    # (le code delete reste inchangé)
    try:
        gef_to_delete = Gef.query.filter_by(numero=gef_numero).first()
        if gef_to_delete:
            db.session.delete(gef_to_delete)
            db.session.commit()
            flash(f"Le GEF N°{gef_numero} a été supprimé avec succès.", 'success')
        else:
            flash(f"Le GEF N°{gef_numero} n'a pas été trouvé.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur est survenue lors de la suppression : {e}", 'danger')
    return redirect(url_for('main.dashboard'))


# === Route 6 : Recherche et Filtrage de GEFs ===
@main_bp.route('/gef/filter')
def filter_gefs():
    # --- 1. Récupération des paramètres de filtre ---
    selected_wilaya = request.args.get('wilaya', type=int)
    selected_commune = request.args.get('commune', type=int)
    selected_agrements = request.args.getlist('agrements', type=int)
    selected_equipements = request.args.getlist('equipements', type=int)
    statut_bureau = request.args.get('statut_bureau')
    situation = request.args.get('situation')
    
    # --- 2. Construction de la requête de base ---
    query = Gef.query.options(
        joinedload(Gef.commune).joinedload(Commune.wilaya),
        joinedload(Gef.agrement_links).joinedload(GefAgrement.agrement_link),
        joinedload(Gef.equipement_links).joinedload(GefEquipement.equipement_link)
    )

    # --- 3. Application des filtres ---
    if selected_wilaya:
        query = query.join(Gef.commune).filter(Commune.code_wilaya == selected_wilaya)
    if selected_commune:
        query = query.filter(Gef.commune_c == selected_commune)
    if statut_bureau:
        query = query.filter(Gef.statut_bureau == statut_bureau)
    if situation:
        query = query.filter(Gef.situation == situation)
    if selected_agrements:
        query = query.join(Gef.agrement_links).filter(GefAgrement.agrement_id.in_(selected_agrements))
    if selected_equipements:
        query = query.join(Gef.equipement_links).filter(GefEquipement.id_type.in_(selected_equipements))

    # --- 4. Exécution de la requête ---
    gefs_results = query.all()

    # --- 5. Chargement des données pour les menus déroulants ---
    try:
        wilayas = Wilaya.query.order_by(Wilaya.nom_wilaya).all()
        agrements = Agrement.query.order_by(Agrement.nom).all()
        type_equipements = TypeEquipement.query.order_by(TypeEquipement.nom_type).all()
        
        communes = []
        if selected_wilaya:
            communes = Commune.query.filter_by(code_wilaya=selected_wilaya).order_by(Commune.nom_commun).all()
            
    except Exception as e:
        flash(f"Erreur de base de données : {e}", "danger")
        wilayas, agrements, type_equipements, communes = [], [], [], []

    # --- 6. Rendu du template ---
    return render_template(
        'filter_gef.html',
        wilayas=wilayas,
        communes=communes,
        agrements=agrements,
        type_equipements=type_equipements,
        gefs_results=gefs_results,
        # Pour conserver l'état du formulaire après soumission
        selected_wilaya=selected_wilaya,
        selected_commune=selected_commune,
        selected_agrements=selected_agrements,
        selected_equipements=selected_equipements,
        statut_bureau=statut_bureau,
        situation=situation
    )


# === SECTION API (pour le JavaScript) ===

@main_bp.route('/api/communes/<int:wilaya_code>')
def get_communes_by_wilaya(wilaya_code):
    """API pour lister les communes d'une wilaya spécifique."""
    # (le code reste inchangé)
    try:
        communes = Commune.query.filter_by(code_wilaya=wilaya_code).order_by(Commune.nom_commun).all()
        communes_list = [{'code': c.code_commu, 'nom': c.nom_commun} for c in communes]
        return jsonify(communes_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/gefs')
def get_gefs():
    """API pour lister tous les GEFs (pour le menu déroulant)"""
    # (le code reste inchangé)
    try:
        database_url = os.environ.get('DATABASE_URL', '')
        # database_url = "postgresql://postgres:12345678@localhost:5432/ogef" 
        parsed = urlparse(database_url)
        env = os.environ.copy()
        if parsed.password: env['PGPASSWORD'] = parsed.password
        env['PGCLIENTENCODING'] = 'latin1'
        cmd = ['psql', '-h', parsed.hostname or 'localhost', '-U', parsed.username or 'postgres', '-d', parsed.path[1:] if parsed.path else 'postgres', '-tAc', "SELECT numero, n_p FROM gef ORDER BY n_p;"]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
        gefs = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 2: gefs.append({'numero': parts[0].strip(), 'nom': parts[1].strip()})
        return jsonify({"gefs": gefs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/gef/<int:gef_numero>')
def get_gef_details(gef_numero):
    """API pour récupérer tous les détails d'un GEF spécifique"""
    # (le code reste inchangé mais vérifié pour observations)
    try:
        database_url = os.environ.get('DATABASE_URL', '')
        # database_url = "postgresql://postgres:12345678@localhost:5432/ogef" 
        parsed = urlparse(database_url)
        env = os.environ.copy()
        if parsed.password: env['PGPASSWORD'] = parsed.password
        env['PGCLIENTENCODING'] = 'latin1'
        details = {}
        queries = {
            # ✅ Requête GEF incluant observations et date_obt
            "gef": f"""
                SELECT 
                    g.numero, g.n_p, g.email, g.adresse, g.statut_bureau, g.situation, 
                    g.observations, TO_CHAR(g.date_obt, 'YYYY-MM-DD'), TO_CHAR(g.date_naiss, 'YYYY-MM-DD'),
                    g.nim, g.nif,
                    c_adresse.nom_commun AS commune_adresse,
                    w_adresse.nom_wilaya AS wilaya_adresse,
                    c_naiss.nom_commun AS commune_naissance,
                    w_naiss.nom_wilaya AS wilaya_naissance
                FROM gef g
                LEFT JOIN commune c_adresse ON g.commune_c = c_adresse.code_commu
                LEFT JOIN wilaya w_adresse ON c_adresse.code_wilaya = w_adresse.code
                LEFT JOIN commune c_naiss ON g.lieu_naiss_cc = c_naiss.code_commu
                LEFT JOIN wilaya w_naiss ON g.lieu_naiss_wc = w_naiss.code
                WHERE g.numero = {gef_numero};
            """,
            "employees": f"SELECT nom, prenom, profile FROM personnel WHERE n_gef = {gef_numero} ORDER BY nom, prenom;",
            "telephones": f"SELECT type_tel, num FROM telephones WHERE n_gef = {gef_numero} ORDER BY type_tel;",
            "equipments": f"SELECT te.nom_type, ge.quantite FROM gef_equipement ge JOIN type_equipement te ON ge.id_type = te.id_type WHERE ge.n_gef = {gef_numero} ORDER BY te.nom_type;",
            "agrements": f"SELECT a.nom, TO_CHAR(ga.date_obtention, 'YYYY-MM-DD') as date_obt_agrement FROM gef_agrements ga JOIN agrements a ON ga.agrement_id = a.id WHERE ga.gef_n = {gef_numero} ORDER BY a.nom;"
            }

        for key, query in queries.items():
            cmd = ['psql', '-h', parsed.hostname or 'localhost', '-U', parsed.username or 'postgres', '-d', parsed.path[1:] if parsed.path else 'postgres', '-tAc', query]
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
            if result.returncode != 0: raise Exception(f"Erreur psql pour {key}: {result.stderr}")
            lines = result.stdout.strip().split('\n')
            data_list = []
            if lines and lines[0]:
                for line in lines:
                    parts = line.split('|')
                    if key == "gef":
                         # ✅ ON VÉRIFIE MAINTENANT 15 COLONNES
                         if len(parts) >= 15:
                            details[key] = {
                                'numero': parts[0], 'nom': parts[1], 'email': parts[2], 'adresse': parts[3], 
                                'statut_bureau': parts[4], 'situation': parts[5], 'observations': parts[6], 
                                'date_obt': parts[7], 'date_naiss': parts[8], 
                                'nim': parts[9], 'nif': parts[10],
                                'commune_adresse': parts[11],
                                'wilaya_adresse': parts[12],
                                'commune_naissance': parts[13],
                                'wilaya_naissance': parts[14]
                            }
                         break
                    elif key == "employees": data_list.append({'nom': parts[0], 'prenom': parts[1], 'profile': parts[2]})
                    elif key == "telephones": data_list.append({'type': parts[0], 'numero': parts[1]})
                    elif key == "equipments": data_list.append({'nom': parts[0], 'quantite': parts[1]})
                    elif key == "agrements": data_list.append({'nom': parts[0], 'date': parts[1]})
            if key != "gef": details[key] = data_list
        return jsonify(details)
    except Exception as e:
        print(f"Erreur API pour get_gef_details : {e}")
        return jsonify({"error": str(e)}), 500