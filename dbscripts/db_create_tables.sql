-- Table: public.tbEntity

DROP TABLE IF EXISTS public."tbEntity";

CREATE TABLE IF NOT EXISTS public."tbEntity"
(
    id integer NOT NULL,
    entity_code integer,
    entity_name varchar(150) COLLATE pg_catalog."default",
    CONSTRAINT "tbEntity_pkey" PRIMARY KEY (id)
);
ALTER TABLE public."tbEntity"
    ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;

DROP TABLE IF EXISTS public."tbCourse";

CREATE TABLE IF NOT EXISTS public."tbCourse"
(
    id integer NOT NULL,
    entity_code integer,
	course_code varchar(50),
    course_name varchar(150) COLLATE pg_catalog."default",
    CONSTRAINT "tbCourse_pkey" PRIMARY KEY (id)
);
ALTER TABLE public."tbCourse"
    ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;

DROP TABLE IF EXISTS public."tbGroup";

CREATE TABLE IF NOT EXISTS public."tbGroup"
(
    id integer NOT NULL,
    entity_code integer,
	course_code varchar(50),
	group_code varchar(50),
    code varchar(50),
    group_name varchar(150) COLLATE pg_catalog."default",
    CONSTRAINT "tbGroup_pkey" PRIMARY KEY (id)
);
ALTER TABLE public."tbGroup"
    ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;

DROP TABLE IF EXISTS public."tbTask";

CREATE TABLE IF NOT EXISTS public."tbTask"
(
    id integer NOT NULL,
    entity_code integer,
	course_code varchar(50),
	group_code varchar(50),
	task_code varchar(50),
    task_name varchar(300) COLLATE pg_catalog."default",
    CONSTRAINT "tbTask_pkey" PRIMARY KEY (id)
);
ALTER TABLE public."tbTask"
    ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;

DROP TABLE IF EXISTS public."tbPlace";

CREATE TABLE IF NOT EXISTS public."tbPlace"
(
    id integer NOT NULL,
    entity_code integer,
	course_code varchar(50),
	group_code varchar(50),
	id_place varchar(100),
	cnpj varchar(50),
    place_name varchar(300) COLLATE pg_catalog."default",
    CONSTRAINT "tbPlace_pkey" PRIMARY KEY (id)
);
ALTER TABLE public."tbPlace"
    ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;

