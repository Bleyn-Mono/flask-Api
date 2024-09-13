import json

from flask import Flask, jsonify, url_for
import unittest
from unittest.mock import mock_open, patch, Mock
from pathlib import Path
from bs4 import BeautifulSoup
from flask_restful import Api, Resource
import xml.etree.ElementTree as ET
import datetime
import report_racers
from main import app, api, IndexApi, NamePage


class TestMonacoFileFlask(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    @patch("builtins.open", new_callable=mock_open,
           read_data="line1\nline2\nline3")
    def test_read_file(self, mock_file_open):
        file_path = Path("test_data.txt")
        expected_content = ["line1", "line2", "line3"]
        mock_content = report_racers.read_data_file(file_path)
        self.assertEqual(mock_content, expected_content)

    @patch('report_racers.read_data_file')
    def test_parse_log(self, mock_read_file_log):
        mock_read_file_log.return_value = ['SVF2018-05-24_12:02:58.917']
        mock_path_log = Path(__file__).resolve().parent / "test"
        mock_result = report_racers.parse_race_file(mock_path_log)
        expected_result_log = {
            'SVF': datetime.datetime(
                2018, 5, 24, 12, 2, 58, 917000)}
        self.assertEqual(mock_result, expected_result_log)

    @patch('report_racers.read_data_file')
    def test_parse_driver(self, mock_read_file_driver):
        mock_read_file_driver.return_value = ['DDR_Daniel_REDBULL']
        mock_path_driver = Path(__file__).resolve().parent / "test"
        result_driver = report_racers.parser_drivers(mock_path_driver)
        expected_result_driver = {'DDR': ['Daniel', 'REDBULL']}
        self.assertEqual(result_driver, expected_result_driver)

    @patch('report_racers.parse_race_file')
    @patch('report_racers.parser_drivers')
    def test_build(self, mock_abbr, mock_str_or_end):
        result_str = {
            'DDR': datetime.datetime(
                2018, 5, 24, 12, 2, 58, 917000)}
        result_end = {
            'DDR': datetime.datetime(
                2018, 5, 24, 12, 3, 40, 678000)}
        mock_str_or_end.side_effect = [result_str, result_end]
        mock_abbr.return_value = {'DDR': ['Daniel', 'REDBULL']}
        result_build = report_racers.build_report('asc')
        expected_result_build = {'00:41.761000': ('DDR', 'Daniel', 'REDBULL')}
        self.assertEqual(result_build, expected_result_build)

    def test_get_racer(self):
        test_data = {'volvo': ('bob', 2), 'redbul': ('liam', 4)}
        name_test = 'liam'
        result_racer_data = report_racers.get_racer_data(test_data, name_test)
        expected_racer_data = {'redbul': ('liam', 4)}
        self.assertEqual(result_racer_data, expected_racer_data)

    @patch('report_racers.build_report')
    def test_order_build(self, mock_order):
        mock_order.return_value = {
            '01:04.415000': (
                'SVF', 'Sebastian Vettel', 'FERRARI'), '01:13.065000': (
                'NHR', 'Nico Hulkenberg', 'RENAULT')}
        response_order_asc = report_racers.build_report('asc')
        expected_order_asc = {
            '01:04.415000': (
                'SVF', 'Sebastian Vettel', 'FERRARI'), '01:13.065000': (
                'NHR', 'Nico Hulkenberg', 'RENAULT')}
        self.assertEqual(response_order_asc, expected_order_asc)

        response_order_desc = report_racers.build_report('desc')
        expected_order_desc = {
            '01:13.065000': (
                'NHR', 'Nico Hulkenberg', 'RENAULT'), '01:04.415000': (
                'SVF', 'Sebastian Vettel', 'FERRARI')}
        self.assertEqual(response_order_desc, expected_order_desc)

    @patch('report_racers.build_report')
    def test_index(self, mock_index_build):
        mock_index_build.return_value = {
            '01:04.415000': (
                'SVF',
                'Sebastian Vettel',
                'FERRARI')}
        response_index = self.app.get('/report')
        self.assertEqual(response_index.status_code, 200)
        soup_index = BeautifulSoup(response_index.data, 'html.parser')
        expected_text_index = 'Sebastian Vettel : 01:04.415000'
        self.assertTrue(expected_text_index in soup_index.get_text())

        response_index_asc = self.app.get('/report?order=asc')
        self.assertEqual(response_index_asc.status_code, 200)
        soup_index_asc = BeautifulSoup(response_index_asc.data, 'html.parser')
        self.assertTrue(expected_text_index in soup_index_asc.get_text())

        response_index_desc = self.app.get('/report?order=desc')
        self.assertEqual(response_index_desc.status_code, 200)
        soup_index_desc = BeautifulSoup(
            response_index_desc.data, 'html.parser')
        self.assertTrue(expected_text_index in soup_index_desc.get_text())

    @patch('report_racers.build_report')
    def test_info_in_drivers(self, mock_drivers_build):
        mock_drivers_build.return_value = {
            '01:04.415000': (
                'SVF',
                'Sebastian Vettel',
                'FERRARI')}
        response_drivers = self.app.get('/report/drivers/')
        self.assertEqual(response_drivers.status_code, 200)
        soup_drivers = BeautifulSoup(response_drivers.data, 'html.parser')
        expected_text_drivers = 'Sebastian Vettel'
        self.assertTrue(expected_text_drivers in soup_drivers.get_text())

        response_drivers_asc = self.app.get('/report/drivers/?order=asc')
        self.assertEqual(response_drivers_asc.status_code, 200)
        soup_drivers_asc = BeautifulSoup(
            response_drivers_asc.data, 'html.parser')
        self.assertTrue(expected_text_drivers in soup_drivers_asc.get_text())

        response_drivers_desc = self.app.get('/report/drivers/?order=desc')
        self.assertEqual(response_drivers.status_code, 200)
        soup_drivers_desc = BeautifulSoup(
            response_drivers_desc.data, 'html.parser')
        self.assertTrue(expected_text_drivers in soup_drivers_desc.get_text())

    @patch('report_racers.build_report')
    def test_name_page(self, mock_name_page):
        mock_name_page.return_value = {
            '01:04.415000': (
                'SVF',
                'Sebastian Vettel',
                'FERRARI')}
        response_name_page = self.app.get('/report/drivers/SVF')
        self.assertEqual(response_name_page.status_code, 200)
        soup_name_page = BeautifulSoup(response_name_page.data, 'html.parser')
        expected_text_name_page_data = 'Rider data : Sebastian Vettel'
        self.assertTrue(
            expected_text_name_page_data in soup_name_page.get_text())
        expected_text_name_page_command = 'Comand data : FERRARI'
        self.assertTrue(
            expected_text_name_page_command in soup_name_page.get_text())
        expected_text_name_page_time = 'Time : 01:04.415000'
        self.assertTrue(
            expected_text_name_page_time in soup_name_page.get_text())


class TestMonacoIndexApi(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.api.add_resource(IndexApi, '/api/v1/report/')
        self.client = app.test_client()
        self.app.testing = True

    @patch('report_racers.build_report')
    def test_index_api_json(self, mock_index_json):
        mock_index_json.return_value = {
            '01:00.000': [
                'DRR',
                'Daniel Ricciardo',
                'RED BULL RACING TAG HEUER']}
        response_index_js = self.client.get('/api/v1/report/?format=json')
        response_index_data = json.loads(response_index_js.data)
        expected_index_json = {
            "01:00.000": [
                "DRR",
                "Daniel Ricciardo",
                "RED BULL RACING TAG HEUER"]}
        self.assertEqual(response_index_js.status_code, 200)
        self.assertEqual(response_index_js.mimetype, 'application/json')
        self.assertEqual(response_index_data, expected_index_json)

    @patch('report_racers.build_report')
    def test_index_api_xml(self, mock_index_xml):
        mock_index_xml.return_value = {
            '01:00.000': [
                'DRR',
                'Daniel Ricciardo',
                'RED BULL RACING TAG HEUER']}
        response_index_xml = self.client.get('/api/v1/report/?format=xml')
        root = ET.Element('drivers')
        driver_element = ET.SubElement(root, 'driver')
        ET.SubElement(driver_element, 'time').text = '01:00.000'
        data_element = ET.SubElement(driver_element, 'data')
        ET.SubElement(data_element, 'code').text = 'DRR'
        ET.SubElement(data_element, 'name').text = 'Daniel Ricciardo'
        ET.SubElement(data_element, 'team').text = 'RED BULL RACING TAG HEUER'
        expected_index_xml = ET.tostring(root, encoding='utf-8', method='xml')
        self.assertEqual(response_index_xml.status_code, 200)
        self.assertEqual(response_index_xml.mimetype, 'text/xml')
        self.assertEqual(response_index_xml.data, expected_index_xml)


class TestMonacoInfoDriver(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.api.add_resource(NamePage, '/api/v1/report/drivers/')
        self.client = app.test_client()
        self.app.config['SERVER_NAME'] = 'localhost'
        self.app.testing = True

    @patch('report_racers.build_report')
    def test_info_driver_js(self, mock_info_build_js):
        mock_info_build_js.return_value = {
            '01:00.000': [
                'DRR',
                'Daniel Ricciardo',
                'RED BULL RACING TAG HEUER']}
        response_info_js = self.client.get(
            '/api/v1/report/drivers/?format=json')
        response_info_data = json.loads(response_info_js.data)
        expected_info_json = {
            '01:00.000': [
                'http://localhost/api/v1/report/drivers/DRR/',
                'Daniel Ricciardo',
                'RED BULL RACING TAG HEUER']}
        self.assertEqual(response_info_js.status_code, 200)
        self.assertEqual(response_info_js.mimetype, 'application/json')
        self.assertEqual(response_info_data, expected_info_json)

    @patch('report_racers.build_report')
    def test_info_driver_xml(self, mock_info_build_xml):
        mock_info_build_xml.return_value = {
            '01:00.000': [
                'DRR',
                'Daniel Ricciardo',
                'RED BULL RACING TAG HEUER']}
        response_info_xml = self.client.get(
            '/api/v1/report/drivers/?format=xml')
        test_time = '01:00.000'
        test_data = ('DRR', 'Daniel Ricciardo', 'RED BULL RACING TAG HEUER')
        with self.app.app_context():
            root = ET.Element('drivers')
            driver_element = ET.SubElement(root, 'driver')
            ET.SubElement(driver_element, 'time').text = test_time
            data_element = ET.SubElement(driver_element, 'data')
            data_url = 'http://localhost/api/v1/report/drivers/DRR/'
            ET.SubElement(data_element, 'code').text = data_url
            ET.SubElement(data_element, 'name').text = test_data[1]
            ET.SubElement(data_element, 'team').text = test_data[2]
            expected_info_xml = ET.tostring(
                root, encoding='utf-8', method='xml')
            self.assertEqual(response_info_xml.status_code, 200)
            self.assertEqual(response_info_xml.mimetype, 'text/xml')
            self.assertEqual(response_info_xml.data, expected_info_xml)


class TestMonacoNamePage(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.api.add_resource(NamePage, '/api/v1/report/drivers/<name>/')
        self.client = app.test_client()
        self.app.testing = True

    @patch('report_racers.build_report')
    @patch('report_racers.get_racer_data')
    def test_name_page_json(self, mock_name_build_json, mock_name_get_json):
        mock_name_build_json.return_value = {
            '01:00.000': [
                'DRR',
                'Daniel Ricciardo',
                'RED BULL RACING TAG HEUER']}
        mock_name_get_json.return_value = {
            '01:00.000': [
                'DRR',
                'Daniel Ricciardo',
                'RED BULL RACING TAG HEUER']}
        response_name_js = self.client.get(
            '/api/v1/report/drivers/DRR/?format=json')
        response_name_data = json.loads(response_name_js.data)
        expected_name_js = {
            '01:00.000': [
                'DRR',
                'Daniel Ricciardo',
                'RED BULL RACING TAG HEUER']}
        self.assertEqual(response_name_js.status_code, 200)
        self.assertEqual(response_name_js.mimetype, 'application/json')
        self.assertEqual(response_name_data, expected_name_js)

    @patch('report_racers.build_report')
    @patch('report_racers.get_racer_data')
    def test_name_page_xml(self, mock_name_build_xml, mock_name_get_xml):
        mock_name_build_xml.return_value = {
            '01:00.000': [
                'DRR',
                'Daniel Ricciardo',
                'RED BULL RACING TAG HEUER']}
        mock_name_get_xml.return_value = {
            '01:00.000': [
                'DRR',
                'Daniel Ricciardo',
                'RED BULL RACING TAG HEUER']}
        response_name_xml = self.client.get(
            '/api/v1/report/drivers/DRR/?format=xml')
        root = ET.Element('drivers')
        driver_element = ET.SubElement(root, 'driver')
        ET.SubElement(driver_element, 'time').text = '01:00.000'
        data_element = ET.SubElement(driver_element, 'data')
        ET.SubElement(data_element, 'code').text = 'DRR'
        ET.SubElement(data_element, 'name').text = 'Daniel Ricciardo'
        ET.SubElement(
            data_element,
            'team').text = 'RED BULL RACING TAG HEUER'
        expected_name_xml = ET.tostring(root, encoding='utf-8', method='xml')
        self.assertEqual(response_name_xml.status_code, 200)
        self.assertEqual(response_name_xml.mimetype, 'text/xml')
        self.assertEqual(response_name_xml.data, expected_name_xml)


if __name__ == '__main__':
    unittest.main()
