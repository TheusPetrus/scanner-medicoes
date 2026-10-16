"""Testes da extração de campos. Rode com: python -m unittest -v"""
import unittest

from scanner import extrair_campos


class TestExtracao(unittest.TestCase):
    def test_campos_com_rotulos(self):
        texto = "Lat: -12.971400 Long: -38.501400\nData: 15/10/2026 Hora: 09:41:07\nFotógrafo: joão da silva"
        r = extrair_campos(texto)
        self.assertEqual(r["latitude"], -12.9714)
        self.assertEqual(r["longitude"], -38.5014)
        self.assertEqual(r["data"], "15/10/2026")
        self.assertEqual(r["horario"], "09:41:07")
        self.assertEqual(r["nome"], "João Da Silva")

    def test_coordenadas_com_virgula_decimal(self):
        r = extrair_campos("Latitude: -12,9714 Longitude: -38,5014")
        self.assertEqual((r["latitude"], r["longitude"]), (-12.9714, -38.5014))

    def test_coordenadas_fora_do_intervalo_sao_descartadas(self):
        r = extrair_campos("Lat: 123.4567 Long: -38.5014")
        self.assertIsNone(r["latitude"])

    def test_nome_com_acento_errado_pelo_ocr(self):
        self.assertEqual(extrair_campos("Fotégrafo: Carlos Mendes")["nome"], "Carlos Mendes")

    def test_texto_vazio_nao_quebra(self):
        r = extrair_campos("")
        self.assertTrue(all(v is None for v in r.values()))

    def test_horario_sem_segundos(self):
        self.assertEqual(extrair_campos("às 7:05")["horario"], "07:05:00")


if __name__ == "__main__":
    unittest.main()
