CREATE OR REPLACE PROCEDURE public.upsert_tbcourse()
 LANGUAGE plpgsql
AS $procedure$
BEGIN
    -- Inserir novos cursos que ainda não existem
    INSERT INTO public.""tbCourse""(entity_code, course_code, course_name)
    SELECT DISTINCT
        CAST(r.entity_code AS integer),
        r.course_code,
        r.course
    FROM public.aux_grupo_estagio r
    WHERE NOT EXISTS (
        SELECT 1
        FROM public.""tbCourse"" c
        WHERE c.entity_code = CAST(r.entity_code AS integer)
          AND c.course_code = r.course_code
    );

    -- Atualizar nomes de curso quando forem diferentes
    UPDATE public.""tbCourse"" c
    SET course_name = r.course
    FROM public.aux_grupo_estagio r
    WHERE c.entity_code = CAST(r.entity_code AS integer)
      AND c.course_code = r.course_code
      AND c.course_name IS DISTINCT FROM r.course;
END;
$procedure$

CREATE OR REPLACE PROCEDURE public.upsert_tbentity()
 LANGUAGE plpgsql
AS $procedure$
BEGIN
    INSERT INTO public.""tbEntity""( entity_code, entity_name)
    SELECT 
		DISTINCT 
		cast(a.entity_code as integer) as entity_code,
		entity
    FROM public.aux_grupo_estagio a
    WHERE NOT EXISTS (
        SELECT 1
        FROM public.""tbEntity"" b
        WHERE b.entity_code = cast(a.entity_code as integer)
    );

    UPDATE public.""tbEntity"" b
    SET entity_name = a.entity
    FROM public.aux_grupo_estagio a
    WHERE b.entity_code = cast(a.entity_code as integer)
      AND b.entity_name <> a.entity;
END;
$procedure$

CREATE OR REPLACE PROCEDURE public.upsert_tbgroup()
 LANGUAGE plpgsql
AS $procedure$
BEGIN
    -- Inserção de novos grupos
    INSERT INTO public.""tbGroup""(entity_code, course_code, group_code, code, group_name)
    SELECT DISTINCT
        CAST(r.entity_code AS integer),
        r.course_code,
        r.group_code,
        r.code,
        r.name
    FROM public.aux_grupo_estagio r
    WHERE NOT EXISTS (
        SELECT 1
        FROM public.""tbGroup"" g
        WHERE g.entity_code = CAST(r.entity_code AS integer)
          AND g.course_code = r.course_code
          --AND isnull(g.group_code,""0"") = isnull(r.group_code,""0"")
          AND g.code = r.code
    );

    -- Atualização apenas quando o nome for diferente
    UPDATE public.""tbGroup"" g
    SET group_name = r.name
    FROM public.aux_grupo_estagio r
    WHERE g.entity_code = CAST(r.entity_code AS integer)
      AND g.course_code = r.course_code
      --AND g.group_code = r.group_code
      AND g.code = r.code
      AND g.group_name IS DISTINCT FROM r.name;
END;
$procedure$


CREATE OR REPLACE PROCEDURE public.upsert_tbplace()
 LANGUAGE plpgsql
AS $procedure$
BEGIN
    -- Inserção dos registros que ainda não existem
    INSERT INTO public.""tbPlace"" (
        entity_code,
        course_code,
        group_code,
        id_place,
        cnpj,
        place_name
    )
    SELECT DISTINCT
        CAST(r.entity_code AS integer),
        r.course_code,
        r.code AS group_code,
        t->>'id' AS id_place,
        t->>'cnpj' AS cnpj,
        t->>'name' AS place_name
    FROM public.aux_grupo_estagio r,
         jsonb_array_elements(r.places) AS t
    WHERE NOT EXISTS (
        SELECT 1
        FROM public.""tbPlace"" p
        WHERE p.entity_code = CAST(r.entity_code AS integer)
          AND p.course_code = r.course_code
          AND p.group_code = r.code
          AND p.id_place = t->>'id'
    );

    -- Atualização do nome e cnpj quando diferentes
    UPDATE public.""tbPlace"" p
    SET 
        cnpj = t->>'cnpj',
        place_name = t->>'name'
    FROM public.aux_grupo_estagio r,
         jsonb_array_elements(r.places) AS t
    WHERE p.entity_code = CAST(r.entity_code AS integer)
      AND p.course_code = r.course_code
      AND p.group_code = r.code
      AND p.id_place = t->>'id'
      AND (
            p.cnpj IS DISTINCT FROM t->>'cnpj' OR
            p.place_name IS DISTINCT FROM t->>'name'
      );
END;
$procedure$

CREATE OR REPLACE PROCEDURE public.upsert_tbtask()
 LANGUAGE plpgsql
AS $procedure$
BEGIN
    -- Inserção das tarefas que ainda não existem
    INSERT INTO public.""tbTask"" (entity_code, course_code, group_code, task_code, task_name)
    SELECT DISTINCT
        CAST(r.entity_code AS integer),
        r.course_code,
        r.code,
        t->>'code' AS task_code,
        t->>'name' AS task_name
    FROM public.aux_grupo_estagio r,
         jsonb_array_elements(r.tasks) AS t
    WHERE NOT EXISTS (
        SELECT 1
        FROM public.""tbTask"" tt
        WHERE tt.entity_code = CAST(r.entity_code AS integer)
          AND tt.course_code = r.course_code
          AND tt.group_code = r.code
          AND tt.task_code = t->>'code'
    );

    -- Atualização quando o nome da tarefa for diferente
    UPDATE public.""tbTask"" tt
    SET task_name = t->>'name'
    FROM public.aux_grupo_estagio r,
         jsonb_array_elements(r.tasks) AS t
    WHERE tt.entity_code = CAST(r.entity_code AS integer)
      AND tt.course_code = r.course_code
      AND tt.group_code = r.code
      AND tt.task_code = t->>'code'
      AND tt.task_name IS DISTINCT FROM t->>'name';
END;
$procedure$



CREATE OR REPLACE PROCEDURE public.upsert_all()
 LANGUAGE plpgsql
AS $procedure$
BEGIN
    CALL public.upsert_tbEntity();
    CALL public.upsert_tbCourse();
    CALL public.upsert_tbGroup();
    CALL public.upsert_tbTask();
    CALL public.upsert_tbPlace();
END;
$procedure$





CREATE OR REPLACE PROCEDURE public.processar_integracao_estagio(IN p_execution_id uuid)
 LANGUAGE plpgsql
AS $procedure$
BEGIN
    -- Registra execução (caso ainda não registrada)
    INSERT INTO public.tbexecucaointegracao (execution_id, data_execucao, status)
    VALUES (p_execution_id, NOW(), 'PENDENTE');

    -- Insere os dados tratados na tblobbyensalamento
    INSERT INTO public.tblobbyensalamento (
        execution_id,
        entitycode,
        coursecode,
        groupcode,
        taskcode,
        id_place,
        place,
        data,
        start_time,
        end_time,
        cpf_estudante,
        integrated
    )
    SELECT
        p_execution_id,
        G.ENTITY_CODE,
        G.COURSE_CODE::varchar,
        G.CODE::varchar,
        T.TASK_CODE::varchar,
        P.ID_PLACE::varchar,
        P.CNPJ,
        A.DATA,
        A.HORA_INICIO::varchar,
        A.HORA_FINAL::varchar,
        A.CPF_ESTUDANTE,
        FALSE
    FROM
        PUBLIC.""aux_agendamento"" A
    JOIN PUBLIC.""tbGroup"" G ON G.CODE = A.CODIGO_GRUPO
    JOIN PUBLIC.""tbTask"" T ON T.GROUP_CODE = A.CODIGO_GRUPO AND T.TASK_NAME = A.TAREFA
    JOIN PUBLIC.""tbPlace"" P ON P.GROUP_CODE = A.CODIGO_GRUPO AND P.ENTITY_CODE = G.ENTITY_CODE AND P.COURSE_CODE = G.COURSE_CODE;
END;
$procedure$


CREATE OR REPLACE PROCEDURE public.truncate_aux_tables()
 LANGUAGE plpgsql
AS $procedure$
BEGIN
    TRUNCATE TABLE public.""aux_agendamento"";
    TRUNCATE TABLE public.""aux_grupo_estagio"";
END;
$procedure$
