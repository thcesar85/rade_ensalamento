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


-- Table: public.aux_agendamento

-- DROP TABLE IF EXISTS public.aux_agendamento;

CREATE TABLE IF NOT EXISTS public.aux_agendamento
(
    cnpj text COLLATE pg_catalog."default",
    codigo text COLLATE pg_catalog."default",
    curso text COLLATE pg_catalog."default",
    escola text COLLATE pg_catalog."default",
    grupo text COLLATE pg_catalog."default",
    codigo_grupo text COLLATE pg_catalog."default",
    estudante text COLLATE pg_catalog."default",
    cpf_estudante text COLLATE pg_catalog."default",
    atividade text COLLATE pg_catalog."default",
    campo_estagio text COLLATE pg_catalog."default",
    tarefa text COLLATE pg_catalog."default",
    codigo_tarefa text COLLATE pg_catalog."default",
    preceptor text COLLATE pg_catalog."default",
    data date,
    dia_semana text COLLATE pg_catalog."default",
    hora_inicio text COLLATE pg_catalog."default",
    hora_final text COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.aux_agendamento
    OWNER to admin;

-- Table: public.aux_grupo_estagio

-- DROP TABLE IF EXISTS public.aux_grupo_estagio;

CREATE TABLE IF NOT EXISTS public.aux_grupo_estagio
(
    id integer NOT NULL DEFAULT nextval('aux_grupo_estagio_id_seq'::regclass),
    entity_code text COLLATE pg_catalog."default",
    entity text COLLATE pg_catalog."default",
    course_code text COLLATE pg_catalog."default",
    course text COLLATE pg_catalog."default",
    group_code text COLLATE pg_catalog."default",
    code text COLLATE pg_catalog."default",
    name text COLLATE pg_catalog."default",
    start_date date,
    end_date date,
    workload integer,
    daily_limit integer,
    weekly_limit integer,
    days boolean[],
    active boolean,
    teachers jsonb,
    preceptors jsonb,
    students jsonb,
    tasks jsonb,
    places jsonb,
    inserted_at timestamp without time zone DEFAULT now(),
    CONSTRAINT aux_grupo_estagio_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.aux_grupo_estagio
    OWNER to admin;


-- Table: public.tbexecucaointegracao

-- DROP TABLE IF EXISTS public.tbexecucaointegracao;

CREATE TABLE IF NOT EXISTS public.tbexecucaointegracao
(
    id integer NOT NULL DEFAULT nextval('tbexecucaointegracao_id_seq'::regclass),
    execution_id uuid NOT NULL,
    data_execucao timestamp without time zone NOT NULL DEFAULT now(),
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'PENDENTE'::character varying,
    erro text COLLATE pg_catalog."default",
    CONSTRAINT tbexecucaointegracao_pkey PRIMARY KEY (id),
    CONSTRAINT tbexecucaointegracao_execution_id_key UNIQUE (execution_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.tbexecucaointegracao
    OWNER to admin;

-- Table: public.tblobbyensalamento

-- DROP TABLE IF EXISTS public.tblobbyensalamento;

CREATE TABLE IF NOT EXISTS public.tblobbyensalamento
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    execution_id uuid NOT NULL,
    entitycode integer,
    coursecode character varying(50) COLLATE pg_catalog."default",
    groupcode character varying(50) COLLATE pg_catalog."default",
    taskcode character varying(50) COLLATE pg_catalog."default",
    id_place character varying(100) COLLATE pg_catalog."default",
    place character varying(150) COLLATE pg_catalog."default",
    data date,
    start_time character varying(150) COLLATE pg_catalog."default",
    end_time character varying(150) COLLATE pg_catalog."default",
    cpf_estudante character varying(150) COLLATE pg_catalog."default",
    integrated boolean DEFAULT false,
    CONSTRAINT tblobbyensalamento_pkey PRIMARY KEY (id),
    CONSTRAINT tblobbyensalamento_execution_id_fkey FOREIGN KEY (execution_id)
        REFERENCES public.tbexecucaointegracao (execution_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.tblobbyensalamento
    OWNER to admin;

-- Table: public.tblogintegracao

-- DROP TABLE IF EXISTS public.tblogintegracao;

CREATE TABLE IF NOT EXISTS public.tblogintegracao
(
    id integer NOT NULL DEFAULT nextval('tblogintegracao_id_seq'::regclass),
    execution_id uuid NOT NULL,
    lobby_id integer,
    response text COLLATE pg_catalog."default",
    status_code integer,
    mensagem text COLLATE pg_catalog."default",
    retorno_data jsonb,
    retorno_erros jsonb,
    data_log timestamp without time zone DEFAULT now(),
    CONSTRAINT tblogintegracao_pkey PRIMARY KEY (id),
    CONSTRAINT tblogintegracao_execution_id_fkey FOREIGN KEY (execution_id)
        REFERENCES public.tbexecucaointegracao (execution_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT tblogintegracao_lobby_id_fkey FOREIGN KEY (lobby_id)
        REFERENCES public.tblobbyensalamento (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.tblogintegracao
    OWNER to admin;