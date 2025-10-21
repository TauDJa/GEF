# app/models.py
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from datetime import datetime

db = SQLAlchemy()

# --- Spatial Layers ---

class Wilaya(db.Model):
    __tablename__ = 'wilaya'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer, unique=True)
    nom_wilaya = db.Column(db.String(254))
    
    # 1-to-Many: A Wilaya has many Communes
    communes = db.relationship('Commune', back_populates='wilaya')

class Commune(db.Model):
    __tablename__ = 'commune'
    code_commu = db.Column(db.Integer, primary_key=True)
    nom_commun = db.Column(db.String(100))
    code_wilaya = db.Column(db.Integer, db.ForeignKey('wilaya.code'))
    
    # Many-to-1: This Commune belongs to one Wilaya
    wilaya = db.relationship('Wilaya', back_populates='communes')
    # 1-to-Many: A Commune has many Gefs
    gefs = db.relationship('Gef', back_populates='commune')

# --- GEF Core ---

class Gef(db.Model):
    __tablename__ = 'gef'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True)
    n_p = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150))
    adresse = db.Column(db.Text)
    statut_bureau = db.Column(db.String(20))
    commune_c = db.Column(db.Integer, db.ForeignKey('commune.code_commu'))
    geom = db.Column(Geometry(geometry_type='POINT', srid=4326))
    situation = db.Column(db.Text, default='actif')
    nim = db.Column(db.Integer)
    nif = db.Column(db.Integer)
    observations = db.Column(db.Text)
    date_obt = db.Column(db.Date)
    date_naiss = db.Column(db.Date)
    #lieu_naiss_wc = db.Column(db.Integer, db.ForeignKey('wilaya.code'))
    #lieu_naiss_cc = db.Column(db.Integer, db.ForeignKey('commune.code_commu'))
    
    # ✅ AJOUTÉ : Champ pour la photo
    photo_filename = db.Column(db.String(255), nullable=True)
    
    # Many-to-1: This Gef belongs to one Commune
    commune = db.relationship('Commune', back_populates='gefs')
    
    # 1-to-Many: A Gef has many Telephones
    telephones = db.relationship('Telephone', back_populates='gef')
    # 1-to-Many: A Gef has many Personnels
    personnels = db.relationship('Personnel', back_populates='gef')
    
    # 1-to-Many: A Gef has many 'GefEquipement' link objects
    # THIS IS THE RENAMED RELATIONSHIP
    equipement_links = db.relationship('GefEquipement', back_populates='gef_link')
    
    # 1-to-Many: A Gef has many 'GefAgrement' link objects
    # THIS IS THE RENAMED RELATIONSHIP
    agrement_links = db.relationship('GefAgrement', back_populates='gef_link')

class Telephone(db.Model):
    __tablename__ = 'telephones'
    id = db.Column(db.Integer, primary_key=True)
    type_tel = db.Column(db.String(30))
    num = db.Column(db.String(50), nullable=False)
    n_gef = db.Column(db.Integer, db.ForeignKey('gef.numero'))
    
    # Many-to-1: This Telephone belongs to one Gef
    gef = db.relationship('Gef', back_populates='telephones')

class Personnel(db.Model):
    __tablename__ = 'personnel'
    id_personnel = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    date_debut_travail = db.Column(db.Date)
    profile = db.Column(db.String(200))
    n_gef = db.Column(db.Integer, db.ForeignKey('gef.numero'))
    
    # Many-to-1: This Personnel belongs to one Gef
    gef = db.relationship('Gef', back_populates='personnels')

# --- Many-to-Many: Equipements ---

class TypeEquipement(db.Model):
    __tablename__ = 'type_equipement'
    id_type = db.Column(db.Integer, primary_key=True)
    nom_type = db.Column(db.String(50), unique=True, nullable=False)
    
    # 1-to-Many: A TypeEquipement has many 'GefEquipement' link objects
    # THIS IS THE RENAMED RELATIONSHIP
    gef_links = db.relationship('GefEquipement', back_populates='equipement_link')

class GefEquipement(db.Model):
    __tablename__ = 'gef_equipement'
    n_gef = db.Column(db.Integer, db.ForeignKey('gef.numero'), primary_key=True)
    id_type = db.Column(db.Integer, db.ForeignKey('type_equipement.id_type'), primary_key=True)
    quantite = db.Column(db.Integer, default=1)
    
    # Many-to-1: This link object points to one Gef
    gef_link = db.relationship('Gef', back_populates='equipement_links', foreign_keys=[n_gef])
    # Many-to-1: This link object points to one TypeEquipement
    equipement_link = db.relationship('TypeEquipement', back_populates='gef_links', foreign_keys=[id_type])

# --- Many-to-Many: Agrements ---

class Agrement(db.Model):
    __tablename__ = 'agrements'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    
    # 1-to-Many: An Agrement has many 'GefAgrement' link objects
    # THIS IS THE RENAMED RELATIONSHIP
    gef_links = db.relationship('GefAgrement', back_populates='agrement_link')

class GefAgrement(db.Model):
    __tablename__ = 'gef_agrements'
    id = db.Column(db.Integer, primary_key=True)
    gef_n = db.Column(db.Integer, db.ForeignKey('gef.numero'))
    agrement_id = db.Column(db.Integer, db.ForeignKey('agrements.id'))
    
    # Many-to-1: This link object points to one Gef
    gef_link = db.relationship('Gef', back_populates='agrement_links', foreign_keys=[gef_n])
    # Many-to-1: This link object points to one Agrement
    agrement_link = db.relationship('Agrement', back_populates='gef_links', foreign_keys=[agrement_id])