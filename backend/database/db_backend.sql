-- Usar la base de datos
USE db_generate_bot;

-- ========================
-- Tabla: roles (para usuarios)
-- ========================
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rol VARCHAR(50) NOT NULL UNIQUE
);

-- ========================
-- Tabla: usuarios
-- ========================
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL,
    FOREIGN KEY (id_rol) REFERENCES roles(id)
);

-- ========================
-- Tabla: paises
-- ========================
CREATE TABLE paises (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pais VARCHAR(100) NOT NULL UNIQUE
);

-- ========================
-- Tabla: ciudades
-- ========================
CREATE TABLE ciudades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ciudad VARCHAR(100) NOT NULL,
    id_pais INT NOT NULL,
    FOREIGN KEY (id_pais) REFERENCES paises(id)
);

-- ========================
-- Tabla: barrios
-- ========================
CREATE TABLE barrios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barrio VARCHAR(100) NOT NULL,
    id_ciudad INT NOT NULL,
    FOREIGN KEY (id_ciudad) REFERENCES ciudades(id)
);

-- ========================
-- Tabla: partidos_politicos
-- ========================
CREATE TABLE partidos_politicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    partido_politico VARCHAR(150) NOT NULL UNIQUE
);

-- ========================
-- Tabla: clubes_futbol
-- ========================
CREATE TABLE clubes_futbol (
    id INT AUTO_INCREMENT PRIMARY KEY,
    club_futbol VARCHAR(150) NOT NULL UNIQUE
);

-- ========================
-- Tabla: ideologia
-- ========================
CREATE TABLE ideologia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ideologia VARCHAR(100) NOT NULL UNIQUE
);

-- ========================
-- Tabla: estilos_musicas
-- ========================
CREATE TABLE estilos_musicas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estilo_musica VARCHAR(100) NOT NULL UNIQUE
);

-- ========================
-- Tabla: generos
-- ========================
CREATE TABLE generos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    genero VARCHAR(100) NOT NULL UNIQUE
);

-- ========================
-- Tabla: intereses
-- ========================
CREATE TABLE intereses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    interes VARCHAR(100) NOT NULL,
    descripcion TEXT
);

-- ========================
-- Tabla: perfiles
-- ========================
CREATE TABLE perfiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL,
    fecha_nacimiento DATE,
    telefono VARCHAR(20),
    cuenta_FB VARCHAR(100),
    cuenta_IG VARCHAR(100),
    cuenta_TW VARCHAR(100),
    cuenta_TK VARCHAR(100),
    password_FB VARCHAR(255),
    password_IG VARCHAR(255),
    password_TW VARCHAR(255),
    password_TK VARCHAR(255),
    id_pais INT,
    id_ciudad INT,
    id_barrio INT,
    calle VARCHAR(255),
    referencia_direccion VARCHAR(255),
    id_partido_politico INT,
    id_club_futbol INT,
    id_ideologia INT,
    id_estilo_musica INT,
    id_genero INT,
    FOREIGN KEY (id_pais) REFERENCES paises(id),
    FOREIGN KEY (id_ciudad) REFERENCES ciudades(id),
    FOREIGN KEY (id_barrio) REFERENCES barrios(id),
    FOREIGN KEY (id_partido_politico) REFERENCES partidos_politicos(id),
    FOREIGN KEY (id_club_futbol) REFERENCES clubes_futbol(id),
    FOREIGN KEY (id_ideologia) REFERENCES ideologia(id),
    FOREIGN KEY (id_estilo_musica) REFERENCES estilos_musicas(id),
    FOREIGN KEY (id_genero) REFERENCES generos(id)
    ,
    id_plantilla INT NULL
);

-- ========================
-- Tabla: plantilla_perfiles
-- ========================
CREATE TABLE plantilla_perfiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_plantilla VARCHAR(150) NOT NULL
);

-- ========================
-- Tabla: registro_plantilla_perfiles
-- ========================
CREATE TABLE registro_plantilla_perfiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_plantilla INT NOT NULL,
    id_pais INT,
    id_ciudad INT,
    id_barrio INT,
    id_partido_politico INT,
    id_club_futbol INT,
    id_ideologia INT,
    id_estilo_musica INT,
    id_genero INT,
    FOREIGN KEY (id_plantilla) REFERENCES plantilla_perfiles(id),
    FOREIGN KEY (id_pais) REFERENCES paises(id),
    FOREIGN KEY (id_ciudad) REFERENCES ciudades(id),
    FOREIGN KEY (id_barrio) REFERENCES barrios(id),
    FOREIGN KEY (id_partido_politico) REFERENCES partidos_politicos(id),
    FOREIGN KEY (id_club_futbol) REFERENCES clubes_futbol(id),
    FOREIGN KEY (id_ideologia) REFERENCES ideologia(id),
    FOREIGN KEY (id_estilo_musica) REFERENCES estilos_musicas(id),
    FOREIGN KEY (id_genero) REFERENCES generos(id)
);

-- ========================
-- Tabla: tareas_programadas
-- ========================
CREATE TABLE tareas_programadas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    observation TEXT,
    payload JSON
);

-- Agregar la constraint FK para `perfiles.id_plantilla` después de crear `plantilla_perfiles`
ALTER TABLE perfiles
    ADD CONSTRAINT fk_perfiles_plantilla
    FOREIGN KEY (id_plantilla) REFERENCES plantilla_perfiles(id);

-- ========================
-- Datos: Ciudades de Paraguay
-- ========================
-- Asegurar que existe Paraguay
INSERT IGNORE INTO paises (pais) VALUES ('Paraguay');

-- Obtener ID de Paraguay
SET @id_paraguay = (SELECT id FROM paises WHERE pais = 'Paraguay');

INSERT INTO ciudades (ciudad, id_pais) VALUES
('ASUNCIÓN', @id_paraguay),
('CONCEPCIÓN', @id_paraguay),
('BELÉN', @id_paraguay),
('HORQUETA', @id_paraguay),
('LORETO', @id_paraguay),
('SAN CARLOS DEL APA', @id_paraguay),
('SAN LÁZARO', @id_paraguay),
('YBY YAÚ', @id_paraguay),
('AZOTE\'Y', @id_paraguay),
('SARGENTO JOSÉ FÉLIX LÓPEZ', @id_paraguay),
('SAN ALFREDO', @id_paraguay),
('PASO BARRETO', @id_paraguay),
('SAN PEDRO DEL YCUAMANDYYÚ', @id_paraguay),
('ANTEQUERA', @id_paraguay),
('CHORÉ', @id_paraguay),
('GENERAL ELIZARDO AQUINO', @id_paraguay),
('ITACURUBÍ DEL ROSARIO', @id_paraguay),
('LIMA', @id_paraguay),
('NUEVA GERMANIA', @id_paraguay),
('SAN ESTANISLAO', @id_paraguay),
('SAN PABLO', @id_paraguay),
('TACUATÍ', @id_paraguay),
('UNIÓN', @id_paraguay),
('25 DE DICIEMBRE', @id_paraguay),
('VILLA DEL ROSARIO', @id_paraguay),
('GENERAL FRANCISCO ISIDORO RESQUÍN', @id_paraguay),
('YATAITY DEL NORTE', @id_paraguay),
('GUAJAYVI', @id_paraguay),
('CAPIIBARY', @id_paraguay),
('SANTA ROSA DEL AGUARAY', @id_paraguay),
('YRYBUCUA', @id_paraguay),
('LIBERACIÓN', @id_paraguay),
('CAACUPÉ', @id_paraguay),
('ALTOS', @id_paraguay),
('ARROYOS Y ESTEROS', @id_paraguay),
('ATYRÁ', @id_paraguay),
('CARAGUATAY', @id_paraguay),
('EMBOSCADA', @id_paraguay),
('EUSEBIO AYALA', @id_paraguay),
('ISLA PUCÚ', @id_paraguay),
('ITACURUBÍ DE LA CORDILLERA', @id_paraguay),
('JUAN DE MENA', @id_paraguay),
('LOMA GRANDE', @id_paraguay),
('MBOCAYATY DEL YHAGUY', @id_paraguay),
('NUEVA COLOMBIA', @id_paraguay),
('PIRIBEBUY', @id_paraguay),
('PRIMERO DE MARZO', @id_paraguay),
('SAN BERNARDINO', @id_paraguay),
('SANTA ELENA', @id_paraguay),
('TOBATÍ', @id_paraguay),
('VALENZUELA', @id_paraguay),
('SAN JOSE OBRERO', @id_paraguay),
('VILLARRICA', @id_paraguay),
('BORJA', @id_paraguay),
('CAPITÁN MAURICIO JOSÉ TROCHE', @id_paraguay),
('CORONEL MARTÍNEZ', @id_paraguay),
('FÉLIX PÉREZ CARDOZO', @id_paraguay),
('GRAL. EUGENIO A. GARAY', @id_paraguay),
('INDEPENDENCIA', @id_paraguay),
('ITAPÉ', @id_paraguay),
('ITURBE', @id_paraguay),
('JOSÉ FASSARDI', @id_paraguay),
('MBOCAYATY', @id_paraguay),
('NATALICIO TALAVERA', @id_paraguay),
('ÑUMÍ', @id_paraguay),
('SAN SALVADOR', @id_paraguay),
('YATAITY', @id_paraguay),
('DOCTOR BOTTRELL', @id_paraguay),
('PASO YOBAI', @id_paraguay),
('TEBICUARY', @id_paraguay),
('CORONEL OVIEDO', @id_paraguay),
('CAAGUAZÚ', @id_paraguay),
('CARAYAÓ', @id_paraguay),
('DR. CECILIO BÁEZ', @id_paraguay),
('SANTA ROSA DEL MBUTUY', @id_paraguay),
('DR. JUAN MANUEL FRUTOS', @id_paraguay),
('REPATRIACIÓN', @id_paraguay),
('NUEVA LONDRES', @id_paraguay),
('SAN JOAQUÍN', @id_paraguay),
('SAN JOSÉ DE LOS ARROYOS', @id_paraguay),
('YHÚ', @id_paraguay),
('DR. J. EULOGIO ESTIGARRIBIA', @id_paraguay),
('R.I. 3 CORRALES', @id_paraguay),
('RAÚL ARSENIO OVIEDO', @id_paraguay),
('JOSÉ DOMINGO OCAMPOS', @id_paraguay),
('MARISCAL FRANCISCO SOLANO LÓPEZ', @id_paraguay),
('LA PASTORA', @id_paraguay),
('3 DE FEBRERO', @id_paraguay),
('SIMÓN BOLIVAR', @id_paraguay),
('VAQUERÍA', @id_paraguay),
('TEMBIAPORÁ', @id_paraguay),
('NUEVA TOLEDO', @id_paraguay),
('CAAZAPÁ', @id_paraguay),
('ABAÍ', @id_paraguay),
('BUENA VISTA', @id_paraguay),
('DR. MOISÉS S. BERTONI', @id_paraguay),
('GRAL. HIGINIO MORINIGO', @id_paraguay),
('MACIEL', @id_paraguay),
('SAN JUAN NEPOMUCENO', @id_paraguay),
('TAVAÍ', @id_paraguay),
('YEGROS', @id_paraguay),
('YUTY', @id_paraguay),
('3 DE MAYO', @id_paraguay),
('ENCARNACIÓN', @id_paraguay),
('BELLA VISTA', @id_paraguay),
('CAMBYRETÁ', @id_paraguay),
('CAPITÁN MEZA', @id_paraguay),
('CAPITÁN MIRANDA', @id_paraguay),
('NUEVA ALBORADA', @id_paraguay),
('CARMEN DEL PARANÁ', @id_paraguay),
('CORONEL BOGADO', @id_paraguay),
('CARLOS ANTONIO LÓPEZ', @id_paraguay),
('NATALIO', @id_paraguay),
('FRAM', @id_paraguay),
('GENERAL ARTIGAS', @id_paraguay),
('GENERAL DELGADO', @id_paraguay),
('HOHENAU', @id_paraguay),
('JESÚS', @id_paraguay),
('JOSÉ LEANDRO OVIEDO', @id_paraguay),
('OBLIGADO', @id_paraguay),
('MAYOR JULIO DIONISIO OTAÑO', @id_paraguay),
('SAN COSME Y DAMIAN', @id_paraguay),
('SAN PEDRO DEL PARANÁ', @id_paraguay),
('SAN RAFAEL DEL PARANÁ', @id_paraguay),
('TRINIDAD', @id_paraguay),
('EDELIRA', @id_paraguay),
('TOMÁS ROMERO PEREIRA', @id_paraguay),
('ALTO VERÁ', @id_paraguay),
('LA PAZ', @id_paraguay),
('YATYTAY', @id_paraguay),
('SAN JUAN DEL PARANÁ', @id_paraguay),
('PIRAPÓ', @id_paraguay),
('ITAPÚA POTY', @id_paraguay),
('SAN JUAN BAUTISTA DE LAS MISIONES', @id_paraguay),
('AYOLAS', @id_paraguay),
('SAN IGNACIO', @id_paraguay),
('SAN MIGUEL', @id_paraguay),
('SAN PATRICIO', @id_paraguay),
('SANTA MARÍA', @id_paraguay),
('SANTA ROSA', @id_paraguay),
('SANTIAGO', @id_paraguay),
('VILLA FLORIDA', @id_paraguay),
('YABEBYRY', @id_paraguay),
('PARAGUARÍ', @id_paraguay),
('ACAHAY', @id_paraguay),
('CAAPUCÚ', @id_paraguay),
('CABALLERO', @id_paraguay),
('CARAPEGUÁ', @id_paraguay),
('ESCOBAR', @id_paraguay),
('LA COLMENA', @id_paraguay),
('MBUYAPEY', @id_paraguay),
('PIRAYÚ', @id_paraguay),
('QUIINDY', @id_paraguay),
('QUYQUYHÓ', @id_paraguay),
('ROQUE GONZALEZ DE SANTACRUZ', @id_paraguay),
('SAPUCÁI', @id_paraguay),
('TEBICUARY-MÍ', @id_paraguay),
('YAGUARÓN', @id_paraguay),
('YBYCUÍ', @id_paraguay),
('YBYTYMÍ', @id_paraguay),
('CIUDAD DEL ESTE', @id_paraguay),
('PRESIDENTE FRANCO', @id_paraguay),
('DOMINGO MARTÍNEZ DE IRALA', @id_paraguay),
('DR. JUAN LEÓN MALLORQUÍN', @id_paraguay),
('HERNANDARIAS', @id_paraguay),
('ITAKYRY', @id_paraguay),
('JUAN E. O\'LEARY', @id_paraguay),
('ÑACUNDAY', @id_paraguay),
('YGUAZÚ', @id_paraguay),
('LOS CEDRALES', @id_paraguay),
('MINGA GUAZÚ', @id_paraguay),
('SAN CRISTOBAL', @id_paraguay),
('SANTA RITA', @id_paraguay),
('NARANJAL', @id_paraguay),
('SANTA ROSA DEL MONDAY', @id_paraguay),
('MINGA PORÁ', @id_paraguay),
('MBARACAYÚ', @id_paraguay),
('SAN ALBERTO', @id_paraguay),
('IRUÑA', @id_paraguay),
('SANTA FE DEL PARANÁ', @id_paraguay),
('TAVAPY', @id_paraguay),
('DR. RAÚL PEÑA', @id_paraguay),
('AREGUÁ', @id_paraguay),
('CAPIATÁ', @id_paraguay),
('FERNANDO DE LA MORA', @id_paraguay),
('GUARAMBARÉ', @id_paraguay),
('ITÁ', @id_paraguay),
('ITAUGUÁ', @id_paraguay),
('LAMBARÉ', @id_paraguay),
('LIMPIO', @id_paraguay),
('LUQUE', @id_paraguay),
('MARIANO ROQUE ALONSO', @id_paraguay),
('NUEVA ITALIA', @id_paraguay),
('ÑEMBY', @id_paraguay),
('SAN ANTONIO', @id_paraguay),
('SAN LORENZO', @id_paraguay),
('VILLA ELISA', @id_paraguay),
('VILLETA', @id_paraguay),
('YPACARAÍ', @id_paraguay),
('YPANÉ', @id_paraguay),
('J. AUGUSTO SALDIVAR', @id_paraguay),
('PILAR', @id_paraguay),
('ALBERDI', @id_paraguay),
('CERRITO', @id_paraguay),
('DESMOCHADOS', @id_paraguay),
('GRAL. JOSÉ EDUVIGIS DÍAZ', @id_paraguay),
('GUAZÚ-CUÁ', @id_paraguay),
('HUMAITÁ', @id_paraguay),
('ISLA UMBÚ', @id_paraguay),
('LAURELES', @id_paraguay),
('MAYOR JOSÉ DEJESÚS MARTÍNEZ', @id_paraguay),
('PASO DE PATRIA', @id_paraguay),
('SAN JUAN BAUTISTA DE ÑEEMBUCÚ', @id_paraguay),
('TACUARAS', @id_paraguay),
('VILLA FRANCA', @id_paraguay),
('VILLA OLIVA', @id_paraguay),
('VILLALBÍN', @id_paraguay),
('PEDRO JUAN CABALLERO', @id_paraguay),
('BELLA VISTA', @id_paraguay),
('CAPITÁN BADO', @id_paraguay),
('ZANJA PYTÃ', @id_paraguay),
('KARAPAÍ', @id_paraguay),
('SALTO DEL GUAIRÁ', @id_paraguay),
('CORPUS CHRISTI', @id_paraguay),
('VILLA CURUGUATY', @id_paraguay),
('VILLA YGATIMÍ', @id_paraguay),
('ITANARÁ', @id_paraguay),
('YPEJHÚ', @id_paraguay),
('FRANCISCO CABALLERO ALVAREZ', @id_paraguay),
('KATUETÉ', @id_paraguay),
('LA PALOMA DEL ESPÍRITU SANTO', @id_paraguay),
('NUEVA ESPERANZA', @id_paraguay),
('YASY CAÑY', @id_paraguay),
('YBYRAROBANÁ', @id_paraguay),
('YBY PYTÁ', @id_paraguay),
('BENJAMÍN ACEVAL', @id_paraguay),
('PUERTO PINASCO', @id_paraguay),
('VILLA HAYES', @id_paraguay),
('NANAWA', @id_paraguay),
('JOSÉ FALCÓN', @id_paraguay),
('TTE. 1° MANUEL IRALA FERNÁNDEZ', @id_paraguay),
('TENIENTE ESTEBAN MARTÍNEZ', @id_paraguay),
('GENERAL JOSÉ MARÍA BRUGUEZ', @id_paraguay),
('MARISCAL JOSÉ FÉLIX ESTIGARRIBIA', @id_paraguay),
('FILADELFIA', @id_paraguay),
('LOMA PLATA', @id_paraguay),
('FUERTE OLIMPO', @id_paraguay),
('PUERTO CASADO', @id_paraguay),
('BAHÍA NEGRA', @id_paraguay),
('CARMELO PERALTA', @id_paraguay);
