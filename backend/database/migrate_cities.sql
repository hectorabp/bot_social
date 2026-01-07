
INSERT IGNORE INTO paises (pais) VALUES ('Paraguay');

INSERT INTO ciudades (ciudad, id_pais)
SELECT cp.nombre_ciudad, (SELECT id FROM paises WHERE pais = 'Paraguay')
FROM ciudad_py cp
WHERE cp.nombre_ciudad NOT IN (SELECT ciudad FROM ciudades);
