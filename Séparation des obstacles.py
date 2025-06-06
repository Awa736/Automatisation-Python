import arcpy

# Définition des chemins
gdb_path = r'C:\Users\NDIOUF\Documents\Carte_Arcgis\PAVE\PAVE.gdb'
couche_originale = f"{gdb_path}\\sig_geosql_voirie_pave_obstacle_ponctuel"
couche_nouvelle = f"{gdb_path}\\sig_geosql_voirie_pave_obstacle_final"

# Liste des champs obstacles à vérifier
obstacles = [
    "p_gril2", "p_trou2", "p_sol", "p_dev2", "p_obs_140", "p_obs_l140",
    "p_obs_90", "p_obsl90", "p_pose", "p_inf220", "p_sup40", "p_saillie",
    "p_contv", "p_abaque", "p_com", "p_signalet", "p_vegeta", "p_arbre",
    "p_fosarbr", "p_obs_n_p", "p_voiture", "p_terrasse", "p_poubelle",
    "p_travaux", "p_ressaut", "p_pente"
]

# Supprimer la couche existante si elle existe
if arcpy.Exists(couche_nouvelle):
    arcpy.Delete_management(couche_nouvelle)

# Lister tous les champs sauf "OBJECTID" et "Shape"
fields = [f.name for f in arcpy.ListFields(couche_originale) if f.name not in ["id", "Shape", "num_photo"]]
print(len(fields))
print([(i, field) for (i, field) in enumerate(fields)])

# Liste pour stocker les nouvelles lignes
new_rows = []

# Lire les données existantes
with arcpy.da.SearchCursor(couche_originale, ["Shape"] + fields) as search_cursor:  # Exclure "indice_dupl"
    for row in search_cursor:
        shape = row[0]  # Géométrie du point
        attributes = list(row[1:])  # Autres champs (y compris num_photo)

        # Trouver les obstacles présents
        obstacles_presentes = [(i, obs) for i, obs in enumerate(obstacles) if row[i + 1] == 1]

        if len(obstacles_presentes) == 1:
            new_attr = attributes[:]
            # 1 seul obstacle : la valeur de répétition vaut 1
            new_attr.append(1)
            # nom du champ d'origine
            new_attr.append(obstacles_presentes[0][1])
            # valeur du champ d'origine
            new_attr.append(row[obstacles_presentes[0][0]])
            
            # Si un seul obstacle, on garde la ligne telle quelle
            new_rows.append((shape, *new_attr))
        elif len(obstacles_presentes) > 1:
            # Si plusieurs obstacles, on crée une ligne par obstacle
            for indice_dupl, obstacle in enumerate(obstacles_presentes):
                new_attr = attributes[:]  # Copier tous les attributs de base
                #print(len(new_attr))
                # Remettre tous les obstacles à 0 sauf celui correspondant
                for i, obs in enumerate(obstacles):
                    #print(fields.index(obs), " -- ", obs, " __ ", obstacle)
                    new_attr[fields.index(obs)] = 1 if obs == obstacle[1] else 0
                # indice de duplicat en fonction de l'indice de la boucle for
                new_attr[-1] = indice_dupl + 1  # Mettre à jour "indice_dupl"
                # nom du champ d'origine
                new_attr.append(obstacle[1])
                # valeur du champ d'origine
                new_attr.append(row[obstacle[0]])
                new_rows.append((shape, *new_attr))


# Créer la nouvelle couche avec la même structure que l'originale
arcpy.CreateFeatureclass_management(gdb_path, "sig_geosql_voirie_pave_obstacle_final",
                                    "POINT", couche_originale, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", couche_originale)
                
# Ajouter le champ "indice_dupl" manquant
arcpy.AddField_management(couche_nouvelle, "indice_dupl", "LONG")
# Ajouter "indice_dupl" à la liste des champs
fields.append("indice_dupl")  

# Ajouter le champ "P_NOM_INI" manquant
arcpy.AddField_management(couche_nouvelle, "P_NOM_INI", "TEXT", field_length=9)
# Ajouter "P_NOM_INI" à la liste des champs
fields.append("P_NOM_INI")  

# Ajouter le champ "indice_dupl" manquant
arcpy.AddField_management(couche_nouvelle, "P_VAL_INI", "LONG")
# Ajouter "P_VAL_INI" à la liste des champs
fields.append("P_VAL_INI")  

print(new_rows[:-2])

# Insérer toutes les nouvelles lignes dans la nouvelle couche
with arcpy.da.InsertCursor(couche_nouvelle, ["Shape"] + fields) as insert_cursor:
    for new_row in new_rows:
        insert_cursor.insertRow(new_row)

print(f"Création de la couche des obstacles finalisée ! Nombre de points insérés : {len(new_rows)}")