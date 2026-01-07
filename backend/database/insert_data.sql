-- Usar la base de datos
USE db_generate_bot;

-- ========================
-- Insertar datos en paises
-- ========================
INSERT INTO paises (pais) VALUES
('Paraguay'),
('Argentina'),
('Brasil'),
('Chile'),
('Colombia'),
('México'),
('España'),
('Estados Unidos');

-- ========================
-- Insertar datos en ciudades (depende de paises)
-- ========================
INSERT INTO ciudades (ciudad, id_pais) VALUES
('Buenos Aires', 1),
('São Paulo', 2),
('Santiago', 3),
('Bogotá', 4),
('Ciudad de México', 5),
('Madrid', 6),
('Nueva York', 7);

-- ========================
-- Insertar datos en barrios (depende de ciudades)
-- ========================
INSERT INTO barrios (barrio, id_ciudad) VALUES
('Palermo', 1),
('Centro', 1),
('Paulista', 2),
('Las Condes', 3),
('Chapinero', 4),
('Polanco', 5),
('Centro', 6),
('Manhattan', 7);

-- ========================
-- Insertar datos en partidos_politicos
-- ========================
INSERT INTO partidos_politicos (partido_politico) VALUES
('Partido Justicialista'),
('Partido dos Trabalhadores'),
('Partido Socialista de Chile'),
('Partido Liberal Colombiano'),
('Partido Revolucionario Institucional'),
('Partido Socialista Obrero Español'),
('Partido Demócrata');

-- ========================
-- Insertar datos en clubes_futbol
-- ========================
INSERT INTO clubes_futbol (club_futbol) VALUES
('Boca Juniors'),
('Santos FC'),
('Colo-Colo'),
('Millonarios'),
('Club América'),
('Real Madrid'),
('New York City FC');

-- ========================
-- Insertar datos en ideologia
-- ========================
INSERT INTO ideologia (ideologia) VALUES
('Liberal'),
('Conservador'),
('Socialista'),
('Anarquista'),
('Ecologista'),
('Feminista'),
('Neutral');

-- ========================
-- Insertar datos en estilos_musicas
-- ========================
INSERT INTO estilos_musicas (estilo_musica) VALUES
('Rock'),
('Salsa'),
('Cumbia'),
('Reggaeton'),
('Jazz'),
('Clásica'),
('Pop');

-- ========================
-- Insertar datos en generos
-- ========================
INSERT INTO generos (genero) VALUES
('Masculino'),
('Femenino'),
('No binario'),
('Otro');

-- ========================
-- Insertar datos en intereses
-- ========================
INSERT INTO intereses (interes, descripcion) VALUES
('Deportes', 'Actividades físicas y deportes'),
('Música', 'Escuchar y tocar música'),
('Tecnología', 'Innovación y gadgets'),
('Arte', 'Pintura, escultura y expresiones artísticas'),
('Viajes', 'Explorar nuevos lugares'),
('Cocina', 'Cocinar y experimentar con recetas'),
('Lectura', 'Libros y literatura');

-- ========================
-- Insertar datos en plantilla_perfiles
-- ========================
INSERT INTO plantilla_perfiles (nombre_plantilla) VALUES
('Plantilla Básica'),
('Plantilla Avanzada'),
('Plantilla Personalizada');

-- ========================
-- Insertar datos en registro_plantilla_perfiles (depende de plantilla_perfiles y otras tablas)
-- ========================
INSERT INTO registro_plantilla_perfiles (id_plantilla, id_pais, id_ciudad, id_barrio, id_partido_politico, id_club_futbol, id_ideologia, id_estilo_musica, id_genero) VALUES
(1, 1, 1, 1, 1, 1, 1, 1, 1),
(2, 2, 2, 2, 2, 2, 2, 2, 2),
(3, 3, 3, 3, 3, 3, 3, 3, 3);

-- ========================
-- Insertar datos en perfiles (depende de muchas tablas)
-- ========================
INSERT INTO perfiles (nombre, apellido, correo, fecha_nacimiento, telefono, cuenta_FB, cuenta_IG, cuenta_TW, cuenta_TK, password_FB, password_IG, password_TW, password_TK, id_pais, id_ciudad, id_barrio, calle, referencia_direccion, id_partido_politico, id_club_futbol, id_ideologia, id_estilo_musica, id_genero, id_plantilla) VALUES
('Juan', 'Pérez', 'juan.perez@example.com', '1990-05-15', '123456789', 'juan.fb', 'juan.ig', 'juan.tw', 'juan.tk', 'passfb', 'passig', 'passtw', 'passtk', 1, 1, 1, 'Calle Falsa 123', 'Cerca del parque', 1, 1, 1, 1, 1, 1),
('María', 'García', 'maria.garcia@example.com', '1985-10-20', '987654321', 'maria.fb', 'maria.ig', 'maria.tw', 'maria.tk', 'passfb2', 'passig2', 'passtw2', 'passtk2', 2, 2, 2, 'Avenida Siempre Viva 456', 'Frente al río', 2, 2, 2, 2, 2, 2);

-- ========================
-- Insertar datos en tareas_programadas (ejemplo, aunque no hay tareas aún)
-- ========================
INSERT INTO tareas_programadas (task_id, status, observation, payload) VALUES
('task-12345', 'PENDING', 'Tarea de ejemplo para crear cuenta', '{"firstName": "Test", "lastName": "User", "email": "test@example.com", "day": 1, "month": 1, "year": 2000, "gender": "Masculino"}'),
('task-67890', 'SUCCESS', 'Tarea completada', '{"firstName": "Otro", "lastName": "Usuario", "email": "otro@example.com", "day": 2, "month": 2, "year": 1995, "gender": "Femenino"}');