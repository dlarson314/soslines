
import numpy as np
import matplotlib.pyplot as mpl
import matplotlib.pyplot as mpl

def row2lat(height, row):
    return 90 - 180 * (row + 0.5) / height


def lat2row(height, lat):
    return int(np.floor((90 - lat) * height / 180.0))


def col2lon(height, col):
    return 180 * (col + 0.5) / height - 180


def lon2col(height, lon):
    return int(np.floor((lon + 180) * height / 180.0))


def latlon2vec(lat, lon):
    cos_lon = np.cos(lon * np.pi / 180)
    sin_lon = np.sin(lon * np.pi / 180)
    cos_lat = np.cos(lat * np.pi / 180)
    sin_lat = np.sin(lat * np.pi / 180)
    vec = np.array((cos_lat * cos_lon, cos_lat * sin_lon, sin_lat))
    return vec


def vec2latlon(vec):
    xy_radius = np.sqrt(vec[0]**2 + vec[1]**2)
    z = vec[2]
    lat = np.arctan2(z, xy_radius) * 180 / np.pi
    lon = np.arctan2(vec[1], vec[0]) * 180 / np.pi
    return lat, lon


class Canvas:
    """
    This is a canvas used for drawing lines, for Science on a Sphere (SOS)
    images.  It contains background data for speeding up line projection
    computations.

    User interface units are given in decimal degrees.  This includes values of
    latitude, longitude, line_width, diameter of circle, etc.

    Conventions are chosen for looking down on the Earth (or other sphere), with
    the +X axis being at lat=0, lon=0, the +Y axis being at lat=0, lon=+90, and
    the +Z axis being at lat=+90.  We use a right-handed XYZ coordinate system.

    We assume a perfect sphere; there are no ellipsoidal WGS84 or other
    corrections.

    The image being generated has the lon=-180 line at the left edge and the
    lon=+180 line at the right edge.  The top edge of the image is at lat=+90
    and the bottom edge is at lat=-90.  Given the finite size of the pixels
    projected onto the sphere, these lines of latitude and longitude correspond
    to the edges of the pixels, not their centers.

    Row 0 is the top row of pixels in the image.  Column 0 is the left-most
    column of pixels in the image.  There are twice as many columns as rows, due
    to the required width:height = 2:1 aspect ratio.

    self.xyz[height,width,3] is a double precision array of unit vectors
        pointing to the center of each pixel on the sphere.  This is used to
        speed up computations.
    self.canvas[height,width] is a floating point grayscale array that is used
        as a temporary working space for building figures (line segments, etc)
        before writing them to the rgba array.  Values of self.canvas should be
        between 0 and 1, inclusive.  This is effectively used as an alpha
        channel for a solid color image being overlayed on the rgba array.
    self.rgba[height,width,4] is a uint8 (unsigned character) RGBA array that
        holds the final image, including an alpha channel.  
    """

    def __init__(self, height=1024):
        width = 2 * height
        self.xyz = np.zeros((height, width, 3), dtype='double')
        self.canvas = np.zeros((height, width), dtype='float')
        self.rgba = np.zeros((height, width, 4), dtype='uint8')
        lon = col2lon(height, np.arange(width))
        cos_lon = np.cos(lon * np.pi / 180)
        sin_lon = np.sin(lon * np.pi / 180)
        for row in range(height):
            lat = row2lat(height, row)
            cos_lat = np.cos(lat * np.pi / 180)
            self.xyz[row,:,0] = cos_lat * cos_lon
            self.xyz[row,:,1] = cos_lat * sin_lon
            self.xyz[row,:,2] = np.sin(lat * np.pi / 180)

    def transfer_canvas_to_rgba(self, color=(255,255,255,255)):
        # https://en.wikipedia.org/wiki/Alpha_compositing
        height = self.xyz.shape[0]
        width = self.xyz.shape[1]
        alpha = color[3] / 255.0 * self.canvas
        alpha_over = alpha + (1 - alpha) * self.rgba[:,:,3] / 255.0
        g = np.where(alpha_over > 0)
        alpha_top = np.zeros((height,width))
        alpha_top[g] = alpha[g] / alpha_over[g]
        alpha_bottom = (1 - alpha) * (self.rgba[:,:,3] / 255.0) 
        alpha_bottom[g] = alpha_bottom[g] / alpha_over[g]
        for i in range(3):
            self.rgba[:,:,i] = alpha_top * color[i] + alpha_bottom * self.rgba[:,:,i] 
        self.rgba[:,:,3] = (alpha_over * 255.0).astype('uint8')
        #print(np.amin(self.rgba), np.amax(self.rgba))
        #print(np.amin(self.canvas), np.amax(self.canvas))
        self.canvas[:,:] = 0

    def imsave(self, filename='test.png', canvas_filename=None):
        mpl.imsave(filename, self.rgba)
        if canvas_filename:
            mpl.imsave(canvas_filename, self.canvas, cmap=mpl.get_cmap('gray'))

    def disk_simple(self, lat, lon, diameter, color=(255,255,255,255), transfer=True):
        """
        ``simple'' versions of the code are not computationally efficient, but
        should still run in a reasonable amount of time.

        lat, lon, diameter are all in degrees
        color = (R,G,B,A), in values from 0 to 255 inclusive.
        A = alpha.  alpha = 255 is fully opaque; alpha = 0 is fully transparent.
        """
        height = self.xyz.shape[0]
        width = self.xyz.shape[1]
        center = latlon2vec(lat, lon)
        radius = 0.5 * diameter 
        dot_limit = np.cos(radius * np.pi / 180)
        for row in range(height):
            dots = np.dot(self.xyz[row,:,:], center)
            g = np.where(dots > dot_limit)[0]
            if len(g) > 0:
                self.canvas[row,g] = 1.0
        if transfer:
            self.transfer_canvas_to_rgba(color=color)

    def circle_simple(self, lat, lon, diameter, line_width=1,
            color=(255,255,255,255), transfer=True):
        """
        ``simple'' versions of the code are not computationally efficient, but
        should still run in a reasonable amount of time.

        color = (R,G,B,A), in values from 0 to 255 inclusive.
        A = alpha.  alpha = 255 is fully opaque; alpha = 0 is fully transparent.
        """
        height = self.xyz.shape[0]
        center = latlon2vec(lat, lon)
        radius = 0.5 * diameter 
        dot_limit0 = np.cos((radius - 0.5 * line_width) * np.pi / 180)
        dot_limit1 = np.cos((radius + 0.5 * line_width) * np.pi / 180)
        for row in range(height):
            dots = np.dot(self.xyz[row,:,:], center)
            g = np.where(np.logical_and(dots < dot_limit0, dots > dot_limit1))[0]
            if len(g) > 0:
                self.canvas[row,g] = 1.0
        if transfer:
            self.transfer_canvas_to_rgba(color=color)

    def line_simple(self, lat_a, lon_a, lat_b, lon_b, line_width=1,
            color=(255,255,255,255), transfer=True):
        """
        ``simple'' versions of the code are not computationally efficient, but
        should still run in a reasonable amount of time.

        color = (R,G,B,A), in values from 0 to 255 inclusive.
        A = alpha.  alpha = 255 is fully opaque; alpha = 0 is fully transparent.
        """
        height = self.xyz.shape[0]
        vec_a = latlon2vec(lat_a, lon_a)
        vec_b = latlon2vec(lat_b, lon_b)
        orth = np.cross(vec_a, vec_b)
        orth = orth / np.sqrt(np.sum(orth**2))
        along_a = np.cross(orth, vec_a)
        along_b = np.cross(orth, vec_b)
        dot_limit_width = np.sin((0.5 * line_width) * np.pi / 180)

        for row in range(height):
            dots1 = np.dot(self.xyz[row,:,:], orth)
            dots2 = np.dot(self.xyz[row,:,:], along_a)
            dots3 = np.dot(self.xyz[row,:,:], along_b)
            g = np.where((np.abs(dots1) < dot_limit_width) * (dots2 > 0) * (dots3 < 0))[0]
            if len(g) > 0:
                self.canvas[row,g] = 1.0
        if transfer:
            self.transfer_canvas_to_rgba(color=color)

    def line_segment_internal(self, lat_a, lon_a, lat_b, lon_b, line_width=1,
            color=(255,255,255,255), transfer=False):
        """
        This is an internal function that is intended only for well-behaved
        short line segments that do not cross the lon=180 line.  It is intended
        to be faster than the line_simple() function.  This function will give
        give incorrect results when the extent of the line goes above or below
        the latitudes of the endpoints, such as when the middle of a segment
        goes over a pole.

        Obsolete comment:
        Note that the full disk for each endpoint may not be plotted for
        latitudes near the poles, due to the disk extending beyond line_width/2
        from the segment endpoint in longitude.  For joining lines or smooth
        curves, this will be irrelevant because the combination of two segments
        will fill out the circle.  However, we will have to separately ensure
        that the endpoints of each line are fully drawn.
        """
        height = self.xyz.shape[0]
        width = self.xyz.shape[1]
        vec_a = latlon2vec(lat_a, lon_a)
        vec_b = latlon2vec(lat_b, lon_b)
        orth = np.cross(vec_a, vec_b)
        orth = orth / np.sqrt(np.sum(orth**2))
        along_a = np.cross(orth, vec_a)
        along_b = np.cross(orth, vec_b)
        dot_limit_width = np.sin((0.5 * line_width) * np.pi / 180)
        dot_limit_width2 = dot_limit_width**2

        max_lat = max(np.abs(lat_a), np.abs(lat_b))
        scale = 1 / np.cos(max_lat * np.pi / 180)
        min_lat = min(lat_a, lat_b) - 0.5 * line_width
        max_lat = max(lat_a, lat_b) + 0.5 * line_width
        min_lon = min(lon_a, lon_b) - 0.5 * line_width * scale
        max_lon = max(lon_a, lon_b) + 0.5 * line_width * scale

        # Yeah, it's a hack.
        if max_lat > 85:
            max_lat = 90
            min_lon = -180
            max_lon = 180
        if min_lat < -85:
            min_lat = -90
            min_lon = -180
            max_lon = 180
        # For wide lines that go over the lon=180 border
        if max_lon > 180 - 0.5*line_width*scale or min_lon < -180+0.5*line_width*scale:
            min_lon = -180
            max_lon = 180

        r0 = max(lat2row(height, max_lat) - 1, 0)
        r1 = min(lat2row(height, min_lat) + 2, height)
        c0 = max(lon2col(height, min_lon) - 1, 0)
        c1 = min(lon2col(height, max_lon) + 2, width)

        canvas = np.zeros((r1-r0, c1-c0), dtype='float')

        for r, row in enumerate(range(r0,r1)):
            dots1 = np.dot(self.xyz[row,c0:c1,:], orth)
            dots2 = np.dot(self.xyz[row,c0:c1,:], along_a)
            dots3 = np.dot(self.xyz[row,c0:c1,:], along_b)
            dist_a2 = dots1**2 + dots2**2  
            dist_b2 = dots1**2 + dots3**2  
            # Fill in the rectangular line segment
            g = np.where((np.abs(dots1) < dot_limit_width) * (dots2 > 0) * (dots3 < 0))[0]
            if len(g) > 0: canvas[r,g] = 1.0
            # Fill in the disk around point A
            g = np.where(dist_a2 < dot_limit_width2)[0]
            if len(g) > 0: canvas[r,g] = 1.0
            # Fill in the disk around point B
            g = np.where(dist_b2 < dot_limit_width2)[0]
            if len(g) > 0: canvas[r,g] = 1.0

        self.canvas[r0:r1,c0:c1] = np.maximum(self.canvas[r0:r1,c0:c1], canvas)

        #self.rgba[r0:r1,c0:c1,1] = 0.5 * self.rgba[r0:r1,c0:c1,1] + 0.5 * 255
        #self.rgba[r0:r1,c0:c1,3] = 0.5 * self.rgba[r0:r1,c0:c1,3] + 0.5 * 255

        if transfer:
            self.transfer_canvas_to_rgba(color=color)

    def line(self, lat_a, lon_a, lat_b, lon_b, line_width=1,
            color=(255,255,255,255), transfer=True):
        """
        color = (R,G,B,A), in values from 0 to 255 inclusive.
        A = alpha.  alpha = 255 is fully opaque; alpha = 0 is fully transparent.
        """
        vec_a = latlon2vec(lat_a, lon_a)
        vec_b = latlon2vec(lat_b, lon_b)
        orth = np.cross(vec_a, vec_b)
        sin_theta = np.sqrt(np.sum(orth**2))
        orth = orth / sin_theta
        along_a = np.cross(orth, vec_a)
        along_b = np.cross(orth, vec_b)
        cos_theta = np.dot(vec_a, vec_b)
        angle = np.arctan2(sin_theta, cos_theta) * 180 / np.pi
        
        max_step = 5  # degrees
        divisions = int(angle / max_step + 1)
        step = angle / divisions
        for d in range(divisions):
            vec0 = vec_a * np.cos(d * step * np.pi/180) + along_a * np.sin(d * step * np.pi/180)
            vec1 = vec_a * np.cos((d+1) * step * np.pi/180) + along_a * np.sin((d+1) * step * np.pi/180)
            lat_0, lon_0 = vec2latlon(vec0)
            lat_1, lon_1 = vec2latlon(vec1)
            self.line_segment_internal(lat_0, lon_0, lat_1, lon_1,
                line_width=line_width, color=color, transfer=False)
            #self.disk(lat_0, lon_0, line_width, color=color, transfer=False)
        #self.disk(lat_b, lon_b, line_width, color=color, transfer=False)

        if transfer:
            self.transfer_canvas_to_rgba(color=color)


    def disk(self, lat, lon, diameter, color=(255,255,255,255), transfer=True):
        height = self.xyz.shape[0]
        width = self.xyz.shape[1]

        center = latlon2vec(lat, lon)
        radius = 0.5 * diameter 
        dot_limit = np.cos(radius * np.pi / 180)

        min_lat = lat - 0.5 * diameter 
        max_lat = lat + 0.5 * diameter 
        
        scale = 1 / np.cos(lat * np.pi / 180)
        min_lon = lon - 0.5 * diameter * scale
        max_lon = lon + 0.5 * diameter * scale

        r0 = max(lat2row(height, max_lat) - 1, 0)
        r1 = min(lat2row(height, min_lat) + 2, height)
        c0 = max(lon2col(height, min_lon) - 1, 0)
        c1 = min(lon2col(height, max_lon) + 2, width)

        canvas = np.zeros((r1-r0, c1-c0), dtype='float')
        for r, row in enumerate(range(r0,r1)):
            dots = np.dot(self.xyz[row,c0:c1,:], center)
            g = np.where(dots > dot_limit)[0]
            if len(g) > 0:
                canvas[r,g] = 1.0

        self.canvas[r0:r1,c0:c1] = np.maximum(self.canvas[r0:r1,c0:c1], canvas)

        self.rgba[r0:r1,c0:c1,0] = 0.5 * self.rgba[r0:r1,c0:c1,0] + 0.5 * 255
        self.rgba[r0:r1,c0:c1,3] = 0.5 * self.rgba[r0:r1,c0:c1,3] + 0.5 * 255

        if transfer:
            self.transfer_canvas_to_rgba(color=color)



def example1():
    c = Canvas(height=256)
    c.disk_simple(40, 0, 90, color=(255,0,0,255))
    c.circle_simple(40, 90, 90, color=(0,0,255,128))
    c.imsave('example1.png')


def example2():
    c = Canvas(height=1024)

    # Lines of latitude, each of which is transferred to the internal rgba storage
    # as it is computed
    for radius in range(10,180,10):
        c.circle_simple(90, 0, 2*radius, color=(0,0,255,128))

    # Lines of longitude, which are kept in the "canvas" layer before being
    # written to rgba, so that they all have the same level of transparency.
    for lon in range(0, 180, 10):
        c.circle_simple(0, lon, 180, transfer=False)
    c.transfer_canvas_to_rgba(color=(255,0,255,128))

    c.imsave('example2.png')


def example3():
    c = Canvas(height=256)
    c.line_simple(0,0,45,90,line_width=5,color=(0,0,255,255))
    c.imsave('example3.png')


def example4():
    c = Canvas(height=1024)
    c.line_segment_internal(0,0,45,120,line_width=5,color=(0,0,255,255), transfer=True)
    c.imsave('example4.png')

def example5():
    c = Canvas(height=2048)
    c.line(0,0,45,179,line_width=5,color=(0,0,255,255), transfer=True)
    c.imsave('example5.png')
        


if __name__ == "__main__":
    #example1()
    #example2()
    #example3()
    #example4()
    example5()


