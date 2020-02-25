# todo: https://pywps.readthedocs.io/en/master/wps.html#wps
# * The input or output can also be result of any OGC OWS service.
# * how to select output format?
# wkt input <wps:ComplexData mimeType="application/wkt"><![CDATA[Polygon((21.98 38.04, 22.4 37.95, 22.12 37.53, 21.98 38.04))]]></wps:ComplexData>

# import owslib.wps
import tempfile
from pywps import FORMATS, Format
from pywps.app import Process
from pywps.app.Common import Metadata
from pywps.inout import ComplexInput, LiteralInput, BoundingBoxInput, ComplexOutput, LiteralOutput
from pywps.response.execute import ExecuteResponse

from processes import gdal_dem_color_cutline
from gdalos import gdal_helper
from gdalos.rectangle import GeoRectangle

czml_format = Format('application/czml+json', extension='.czml')
wkt_format = Format('application/wkt', extension='.wkt')
DEFAULT_RASTER = 'static/sample/srtm_x35_y32.tif'

# import pywps.inout.literaltypes
# pywps.inout.literaltypes.LITERAL_DATA_TYPES


class GdalDem(Process):
    def __init__(self):
        inputs = [
            ComplexInput('r', 'input raster', supported_formats=[FORMATS.GEOTIFF],
                         min_occurs=0, max_occurs=1, default=None),
            LiteralInput('output_czml', 'make output as czml', data_type='boolean',
                         min_occurs=0, max_occurs=1, default=True),
            LiteralInput('output_tif', 'make output as tift', data_type='boolean',
                         min_occurs=0, max_occurs=1, default=False),
            ComplexInput('color_palette', 'color palette', supported_formats=[FORMATS.TEXT],
                         min_occurs=0, max_occurs=1, default=None),
            ComplexInput('cutline', 'input vector cutline',
                         supported_formats=[FORMATS.GML],
                         # crss=['EPSG:4326', ], metadata=[Metadata('EPSG.io', 'http://epsg.io/'), ],
                         min_occurs=0, max_occurs=1, default=None),
            BoundingBoxInput('extent', 'extent BoundingBox',
                             crss=['EPSG:4326', ], metadata=[Metadata('EPSG.io', 'http://epsg.io/'), ],
                             min_occurs=0, max_occurs=1, default=None)
        ]
        outputs = [
            LiteralOutput('r', 'input raster name', data_type='string'),
            ComplexOutput('tif', 'result as GeoTIFF', supported_formats=[FORMATS.GEOTIFF]),
            ComplexOutput('czml', 'result as CZML', supported_formats=[czml_format])
        ]

        super().__init__(
            self._handler,
            identifier='crop_color',
            version='0.1',
            title='crops to an extent and/or to a cutline polygon[s] and/or makes a color relief',
            abstract='returns a color relief of the input raster inside the given extent or cutline polygon[s]',
            inputs=inputs,
            outputs=outputs,
            # metadata=[Metadata('bla'), Metadata('bla')],
            # profile='',
            # store_supported=True,
            # status_supported=True
        )


    def _handler(self, request, response: ExecuteResponse):
        raster_filename = request.inputs['r'][0].file

        output_czml = request.inputs['output_czml'][0].data
        output_tif = request.inputs['output_tif'][0].data
        if output_czml or output_tif:
            cutline = request.inputs['cutline'][0].file if 'cutline' in request.inputs else None
            color_palette = request.inputs['color_palette'][0].file if 'color_palette' in request.inputs else None
            extent = request.inputs['extent'][0].data if 'extent' in request.inputs else None
            if extent is not None:
                # I'm not sure why the extent is in format miny, minx, maxy, maxx
                extent = [float(x) for x in extent]
                extent = GeoRectangle.from_min_max(extent[1], extent[3], extent[0], extent[2])

            czml_output_filename = tempfile.mktemp(suffix=czml_format.extension) if output_czml else None
            tif_output_filename = tempfile.mktemp(suffix=FORMATS.GEOTIFF.extension) if output_tif else None

            # gdal_out_format = 'czml' if output_format.extension == '.czml' else 'GTiff'
            # gdal_out_format = 'MEM' if is_czml else output_format
            gdal_out_format = 'GTiff' if output_tif else 'MEM'

            src_ds = gdal_helper.open_ds(raster_filename)
            if src_ds is None:
                raise Exception('cannot open file {}'.format(raster_filename))

            ds = gdal_dem_color_cutline.czml_gdaldem_crop_and_color(
                ds=src_ds,
                czml_output_filename=czml_output_filename,
                out_filename=tif_output_filename,
                extent=extent, cutline=cutline,
                color_palette=color_palette,
                output_format=gdal_out_format)
            del ds
            del src_ds
            if output_tif:
                response.outputs['tif'].output_format = FORMATS.GEOTIFF
                response.outputs['tif'].file = tif_output_filename
            if output_czml:
                response.outputs['czml'].output_format = czml_format
                response.outputs['czml'].file = czml_output_filename

        response.outputs['r'].data = raster_filename
        # response.outputs['response'].uom = UOM('unity')
        return response
