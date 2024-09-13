from flask import Flask, render_template, request, jsonify, Response, url_for
from flask_restful import Api, Resource
import report_racers
from flasgger import Swagger
import xml.etree.ElementTree as ET

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)


@app.route('/report')
def index():
    '''This route handles the main page'''
    order = request.args.get('order', 'asc')
    sorted_data = report_racers.build_report(order)
    return render_template('index.html', report=sorted_data)


@app.route('/report/drivers/')
def info_in_drivers():
    '''shows a list of driver's names and codes. The code should be a link to info about drivers'''
    order = request.args.get('order', 'asc')
    sorted_data = report_racers.build_report(order)
    return render_template('info_in_drivers.html', report=sorted_data)


@app.route('/report/drivers/<name>')
def name_page(name):
    '''Returns a page with the name'''
    order = request.args.get('order', 'asc')
    sorted_data = report_racers.build_report(order)
    result, racer_data = report_racers.get_racer_data(
        sorted_data, name).popitem()
    return render_template('name_page.html', racer=racer_data, report=result)


class RenderXML:
    """
    A class for rendering race data as XML.
    This class provides methods to convert race data stored in a dictionary
    to an XML format suitable for web responses.
    """
    @staticmethod
    def dictxml(data):
        """
        Convert a dictionary of race data to an XML string.
        This method takes a dictionary where the keys are timestamps and the values are tuples
        containing driver information (code, name, team). It constructs an XML tree with this data.
        Args:
            data (dict): A dictionary with timestamps as keys and tuples of driver information as values.
                         Example: {'01:00:00': ('DRR', 'Daniel Ricardo', 'Ferrari')}
        Returns:
            bytes: An XML string representing the race data encoded in UTF-8.
        """
        root = ET.Element('drivers')
        for time, data in data.items():
            driver_element = ET.SubElement(root, 'driver')
            ET.SubElement(driver_element, 'time').text = time
            data_element = ET.SubElement(driver_element, 'data')
            ET.SubElement(data_element, 'code').text = data[0]
            ET.SubElement(data_element, 'name').text = data[1]
            ET.SubElement(data_element, 'team').text = data[2]
        return ET.tostring(root, encoding='utf-8', method='xml')

    def render(self, data):
        return Response(self.dictxml(data), mimetype='text/xml')


class RenderJson:
    @staticmethod
    def dictjson(data):
        return jsonify(data)

    def render(self, data):
        return self.dictjson(data)


class RenderMixin:
    """
    A mixin class for rendering data in multiple formats.

    This class provides a mechanism to render data in different formats such as JSON and XML.
    It uses the `renders` dictionary to map format names to their respective rendering classes.
    """
    renders = {
        "json": RenderJson,
        "xml": RenderXML
    }

    def render(self, data, format="json"):
        """
        Render data in the specified format.
        This method takes data and a format name, retrieves the corresponding rendering class
        from the `renders` dictionary, and uses it to render the data. If the specified format
        is not supported, it raises a ValueError.
        Args:
            data (dict): The data to be rendered.
            format (str): The format in which to render the data. Default is "json".
        Returns:
            Response: A Flask Response object containing the rendered data.
        Raises:
            ValueError: If the specified format is not supported.
        """
        render_ = self.renders.get(format)
        if not render_:
            raise ValueError(
                f"Format does not support. Support formats are {
                    self.renders}")
        return render_().render(data)


class IndexApi(Resource, RenderMixin):
    """
    API resource for the main page.

    This class handles GET requests to the main page, allowing users to retrieve
    race reports in different formats and orders.

    Inherits from:
        Resource: Base class for all Flask-RESTful resources.
        RenderMixin: Mixin class providing rendering capabilities in multiple formats.
    """

    def get(self):
        """
        This route handles the main page.
        ---
        parameters:
          - name: order
            in: query
            type: string
            default: asc
            description: The order of sorting (asc or desc).
        responses:
          200:
            description: This route retrieves race report data, sorts it according to the specified order,
        and returns it in the specified format (default is JSON).
        """
        order = request.args.get('order', 'asc')
        format_param = request.args.get('format', 'json')
        sorted_data = report_racers.build_report(order)
        return self.render(sorted_data, format_param)


class InfoDriver(Resource, RenderMixin):
    """
    API resource for displaying driver information.
    This class handles GET requests to display a list of driver names and codes.
    The driver codes are presented as links to additional information about each driver.
    Inherits from:
        Resource: Base class for all Flask-RESTful resources.
        RenderMixin: Mixin class providing rendering capabilities in multiple formats.
    """

    def get(self):
        """
        Shows a list of driver's names and codes. The code should be a link to info about drivers.
        ---
        parameters:
          - name: order
            in: query
            type: string
            default: asc
            description: The order of sorting (asc or desc).
        responses:
          200:
            description: This route retrieves driver information, sorts it according to the specified order,
        and returns it in the specified format (default is JSON).
        """
        order = request.args.get('order', 'asc')
        format_param = request.args.get('format', 'json')
        sorted_data_info = report_racers.build_report(order)
        for time, race_result in sorted_data_info.items():
            sorted_data_info[time] = (
                url_for(
                    'namepage',
                    name=race_result[0],
                    _external=True),
                race_result[1],
                race_result[2])
        return self.render(sorted_data_info, format_param)


class NamePage(Resource, RenderMixin):
    """
    API resource for displaying driver-specific information.
    This class handles GET requests to display information about a specific driver.
    Inherits from:
        Resource: Base class for all Flask-RESTful resources.
        RenderMixin: Mixin class providing rendering capabilities in multiple formats.
    """

    def get(self, name):
        """
        Returns a page with the name.
        It returns the main report in HTML format.
        ---
        parameters:
          - name: name
            in: path
            type: string
            required: true
            description: The name of the driver.
          - name: order
            in: query
            type: string
            default: asc
            description: The order of sorting (asc or desc).
        responses:
          200:
            description: The format of the response (json or xml).
        """
        order = request.args.get('order', 'asc')
        format_param = request.args.get('format', 'json')
        sorted_data = report_racers.build_report(order)
        page = report_racers.get_racer_data(sorted_data, name)
        return self.render(page, format_param)


api.add_resource(InfoDriver, '/api/v1/report/drivers/')
api.add_resource(IndexApi, '/api/v1/report/')
api.add_resource(NamePage, '/api/v1/report/drivers/<name>/')

if __name__ == '__main__':
    app.run(debug=True)
