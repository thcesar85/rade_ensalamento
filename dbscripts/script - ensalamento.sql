SELECT 
	distinct
	entity_code,
	entity
FROM public.aux_grupo_estagio;

SELECT
	 distinct
	 entity_code,
	 course_code,
	 course,

FROM public.aux_grupo_estagio r;


SELECT
	 distinct
	 entity_code,
	 course_code,
	 group_code,
	 code, 
	 name
FROM public.aux_grupo_estagio r;





SELECT
	DISTINCT
	r.entity_code as entity_code,
	r.course_code as course_code,
    r.code AS grupo_code,
    t->>'code' AS tarefa_codigo,
    t->>'name' AS tarefa_nome
FROM public.aux_grupo_estagio r,
     jsonb_array_elements(r.tasks) AS t;


SELECT
	DISTINCT
	r.entity_code as entity_code,
    t->>'id' AS id_place,
    t->>'cnpj' AS cnpj,
	t->>'name' as name
FROM public.aux_grupo_estagio r,
     jsonb_array_elements(r.places) AS t;