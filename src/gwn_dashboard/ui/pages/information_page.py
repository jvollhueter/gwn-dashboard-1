"""Information, contact and legal placeholders."""

import streamlit as st

from gwn_dashboard.ui.navigation import current_information_section


class InformationPage:
    """Render technical information and clearly marked legal placeholders."""

    def render(self) -> None:
        section = current_information_section()
        st.markdown('<div class="viewer-information-shell">', unsafe_allow_html=True)
        st.title("Information")
        if section == "contact":
            st.header("Kontakt")
            st.info("Hier ist vor der Veröffentlichung der freigegebene fachliche Kontakt des LfULG einzutragen.")
        elif section == "imprint":
            st.header("Impressum")
            st.warning("Das verbindliche Impressum muss durch die zuständige Stelle des LfULG freigegeben und hier ergänzt werden.")
        elif section == "privacy":
            st.header("Datenschutzerklärung")
            st.warning("Die Datenschutzerklärung muss anhand des tatsächlichen Hostings und der verarbeiteten Nutzungsdaten freigegeben werden.")
        else:
            st.header("Daten und Methodik")
            st.markdown(
                """
                Die Anwendung stellt Zeitreihen, räumliche Vergleiche und statistische
                Auswertungen zur Grundwasserneubildung bereit. Die GWN wird aus den
                Komponenten `rg1` und `rg2` gebildet und auf Ebene der ausgewählten
                Grundwasserkörper ausgewertet.

                **Referenzperiode:** 1961–1990  
                **Vergleichsperiode:** 1991–2020  
                **Einheit:** mm/a
                """
            )
        st.markdown('</div>', unsafe_allow_html=True)
