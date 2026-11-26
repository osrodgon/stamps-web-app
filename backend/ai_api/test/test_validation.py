"""Tests for the support checker (plan step A9).

Fixed facts, no network and no database: what the sources said, what the model
wrote, and what survives.
"""

from ai_api.validation import check_support


FACTS = {
    "serie_info": {
        "issue_name": "Navidad",
        "year": "1986",
        "issue_date": "16 noviembre 1986",
        "printer": "Fábrica Nacional de Moneda y Timbre",
        "print_type": "Offset",
        "engraver": "Felipe de Bigarny",
        "print_run": "4.000.000",
        "perforation": "13 3/4",
    },
    "stamps": [
        {
            "edifil_code": "2868",
            "fesofi_code": "2884",
            "face_value": "48 pta",
            "motive": "Natividad. Toledo",
            "color": "multicolor",
            "perforation": "13 3/4",
            "total_print_run": "4.000.000",
            "desc_snippet": "Papel estucado. Sello de la serie Navidad.",
        }
    ],
}


def result(**overrides):
    """A model answer whose series fields match the facts."""
    data = {
        "issue_name": "Navidad",
        "issue_date": "1986-11-16",
        "artist": "Felipe de Bigarny",
        "printer": "Fábrica Nacional de Moneda y Timbre",
        "print_type": "Offset",
        "perforation": "13 3/4",
        "paper_type": "Estucado",
        "stamp_type": None,
        "total_printed": 4000000,
        "description": "Sello dedicado a la Natividad de Toledo.",
        "stamps": [
            {
                "edifil_code": "2868",
                "fesofi_code": "2884",
                "face_value": "48 pta",
                "motive": "Natividad. Toledo",
                "color": "multicolor",
                "perforation": "13 3/4",
                "total_print_run": "4.000.000",
                "amount_printed": 4000000,
                "description": "Natividad de Toledo.",
            }
        ],
    }
    data.update(overrides)
    return data


class TestSeries:
    """A series field stays only when the facts carry it."""

    def test_a_supported_value_survives(self):
        gaps = check_support(result(), FACTS)

        assert "printer" not in [gap["field"] for gap in gaps]

    def test_case_accents_and_spacing_do_not_matter(self):
        data = result(printer="fabrica nacional de moneda y timbre")

        check_support(data, FACTS)

        assert data["printer"] == "fabrica nacional de moneda y timbre"

    def test_a_reformatted_number_is_the_same_number(self):
        data = result(total_printed=4000000)

        check_support(data, FACTS)

        assert data["total_printed"] == 4000000

    def test_a_different_number_is_dropped(self):
        data = result(total_printed=1000)

        gaps = check_support(data, FACTS)

        assert data["total_printed"] is None
        assert "total_printed" in [gap["field"] for gap in gaps]

    def test_an_iso_date_matches_the_written_one(self):
        data = result(issue_date="1986-11-16")

        check_support(data, FACTS)

        assert data["issue_date"] == "1986-11-16"

    def test_a_different_date_is_dropped(self):
        data = result(issue_date="1986-11-17")

        gaps = check_support(data, FACTS)

        assert data["issue_date"] is None
        assert "issue_date" in [gap["field"] for gap in gaps]

    def test_an_invented_artist_is_dropped(self):
        data = result(artist="Bartolomé Coromina")

        gaps = check_support(data, FACTS)

        assert data["artist"] is None
        assert "artist" in [gap["field"] for gap in gaps]

    def test_a_value_the_source_text_mentions_is_kept(self):
        data = result(paper_type="Estucado")

        check_support(data, FACTS)

        assert data["paper_type"] == "Estucado"

    def test_a_value_the_source_text_does_not_mention_is_dropped(self):
        data = result(paper_type="Japonés", stamp_type="Carné")

        gaps = check_support(data, FACTS)

        assert data["paper_type"] is None
        assert data["stamp_type"] is None
        assert {"paper_type", "stamp_type"} <= {gap["field"] for gap in gaps}

    def test_a_field_the_facts_leave_empty_is_dropped(self):
        facts = dict(FACTS, serie_info=dict(FACTS["serie_info"], perforation=None))
        data = result(perforation="13 1/4")

        gaps = check_support(data, facts)

        assert data["perforation"] is None
        assert "perforation" in [gap["field"] for gap in gaps]

    def test_the_description_survives(self):
        data = result()

        check_support(data, FACTS)

        assert data["description"].startswith("Sello dedicado")

    def test_an_empty_claim_is_not_a_gap(self):
        data = result(printer=None, artist="n/a")

        gaps = check_support(data, FACTS)

        assert "printer" not in [gap["field"] for gap in gaps]
        assert "artist" not in [gap["field"] for gap in gaps]


class TestStamps:
    """A stamp is checked against the facts of the stamp with that code."""

    def test_a_supported_stamp_survives(self):
        data = result()

        gaps = check_support(data, FACTS)

        assert data["stamps"][0]["edifil_code"] == "2868"
        assert "stamp.edifil_code" not in [gap["field"] for gap in gaps]

    def test_an_invented_code_is_dropped(self):
        data = result()
        data["stamps"][0]["edifil_code"] = "9999"

        gaps = check_support(data, FACTS)

        assert data["stamps"][0]["edifil_code"] is None
        assert "stamp.edifil_code" in [gap["field"] for gap in gaps]
        # The Fesofi code is real, so it stays: the row is still identified.
        assert data["stamps"][0]["fesofi_code"] == "2884"

    def test_a_stamp_without_a_known_code_is_dropped_whole(self):
        data = result()
        data["stamps"][0]["edifil_code"] = "9999"
        data["stamps"][0]["fesofi_code"] = "8888"

        gaps = check_support(data, FACTS)

        assert data["stamps"][0]["edifil_code"] is None
        assert data["stamps"][0]["fesofi_code"] is None
        assert {"stamp.edifil_code", "stamp.fesofi_code"} <= {
            gap["field"] for gap in gaps
        }

    def test_a_stamp_matched_by_its_fesofi_code_is_kept(self):
        data = result()
        data["stamps"][0]["edifil_code"] = None

        check_support(data, FACTS)

        assert data["stamps"][0]["edifil_code"] is None
        assert data["stamps"][0]["face_value"] == "48 pta"

    def test_an_invented_face_value_is_dropped(self):
        data = result()
        data["stamps"][0]["face_value"] = "48 euros"

        check_support(data, FACTS)

        assert data["stamps"][0]["face_value"] is None

    def test_an_invented_colour_is_dropped(self):
        data = result()
        data["stamps"][0]["color"] = "azul"

        check_support(data, FACTS)

        assert data["stamps"][0]["color"] is None

    def test_the_stamp_description_survives(self):
        data = result()

        check_support(data, FACTS)

        assert data["stamps"][0]["description"] == "Natividad de Toledo."


class TestGaps:
    """What was dropped is said, without flooding the response."""

    def test_a_fully_supported_result_has_no_gaps(self):
        assert check_support(result(), FACTS) == []

    def test_the_gaps_are_capped(self):
        stamps = [
            {"edifil_code": f"1{index}", "face_value": "1", "color": "rojo"}
            for index in range(50)
        ]

        gaps = check_support(result(stamps=stamps), FACTS)

        assert len(gaps) <= 20
