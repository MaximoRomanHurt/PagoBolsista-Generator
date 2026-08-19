from src.controllers.bolsista_controller import BolsistaController


def test_declaracion_filename_uses_user_names():
    name = BolsistaController.build_output_name(
        "declaracion",
        {
            "nombres": "Maximo Lenny",
            "ap_paterno": "Roman",
            "ap_materno": "Hurtado",
        },
    )

    assert name == "declaracion_jurada_maximo_lenny_roman_hurtado.pdf"


def test_informe_filename_uses_user_names():
    name = BolsistaController.build_output_name(
        "informe",
        {
            "de_nombre": "Ana Patricia Gomez",
        },
    )

    assert name == "informe_actividades_ana_patricia_gomez.pdf"
