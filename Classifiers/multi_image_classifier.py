import glob
from osgeo import gdal
import os
from scipy.ndimage.morphology import binary_dilation, binary_fill_holes
from scipy.ndimage import median_filter, binary_dilation
from scipy import ndimage
from skimage.filters.rank import median
from skimage.morphology import disk
import os
import timeit
import math
import pandas
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn import tree, metrics
import rasterio
from rasterio import plot
from matplotlib import pyplot as plt
from matplotlib.widgets import Button
from matplotlib.patches import Rectangle
from joblib import dump, load


class pickData(object):
    text_template = 'x: %0.2f\ny: %0.2f'
    x, y = 0.0, 0.0
    xoffset, yoffset = -20, 20
    text_template = 'x: %0.2f\ny: %0.2f'

    def __init__(self, ax):
        self.ax = ax
        self.events = []
        self.points = []
        self.rects = []

    def clear(self, event):
        # Clear the most recent box of pointd
        self.events = []
        self.X0 = None

        # Remove all plotted picked points
        self.rect.remove()
        for p in self.points:
            if p:
                p.remove()

        # Remove most recent rectangle
        self.rects.pop(-1)
        self.points = []
        self.rects = []
        self.rect = None
        print('Cleared')

    def done(self, event):
        # All done picking points
        plt.close('all')
        print('All Done')

    def draw_box(self, event):
        # Draw the points box onto the image
        width = self.events[1][0] - self.events[0][0]
        height = self.events[1][1] - self.events[0][1]
        r = Rectangle(
            self.events[0],
            width,
            height,
            color='red',
            fill=False
        )
        self.rect = self.ax.add_patch(r)
        self.rects.append(r)

        for p in self.points:
            p.remove()
        self.points = []

        event.canvas.draw()

    def __call__(self, event):
        # Call the events
        self.event = event

        if not event.dblclick:
            return 0

        self.x, self.y = event.xdata, event.ydata 
        self.events.append((self.x, self.y))
        self.events = list(set(self.events))

        if self.x is not None:
            # Plot where the picked point is
            self.points.append(self.ax.scatter(self.x, self.y))
            event.canvas.draw()

        if len(self.events) == 2:
            self.draw_box(event)
            self.events = []


def dataBox2df(sample, bandnames):
    height = sample.shape[0] * sample.shape[1]
    matrix = np.zeros([height, sample.shape[2]])
    n = 0
    for i in range(sample.shape[0]):
        for j in range(sample.shape[1]):
            matrix[n, :] = sample[i, j, :]
            n +=1

    return pandas.DataFrame(matrix, columns=bandnames)


def generateTrainingData(image, surface_class, bandnames):
    rgb = image[:, :, [6, 5, 1]]
    rgb[rgb == -9999] = np.nan
    bottom = np.nanpercentile(rgb, 5, axis=(0,1))
    top = np.nanpercentile(rgb, 95, axis=(0,1))
    rgb = np.clip(rgb, bottom, top)
    rgb = (
        rgb-np.nanmin(rgb, axis=(0,1))
    ) / (
        np.nanmax(rgb, axis=(0,1)) 
        - np.nanmin(rgb, axis=(0,1))
    )

    # Get Water data
    fig = plt.figure()
    t = plt.gca()
    im = plt.imshow(rgb)

    PD = pickData(t)

    axclear = plt.axes([0.0, 0.0, 0.1, 0.1])
    bclear = Button(plt.gca(), 'Clear')
    bclear.on_clicked(PD.clear)

    axdone = plt.axes([0.2, 0.0, 0.1, 0.1])
    bdone = Button(plt.gca(), 'Done')
    bdone.on_clicked(PD.done)

    fig.canvas.mpl_connect('button_press_event', PD)

    im.set_picker(5) # Tolerance in points

    plt.show()

    # Convert rectangles to DF 
    df = pandas.DataFrame()
    for rect in PD.rects:
        # Get indexes at bottom left
        botleft = rect.get_xy()
        botleft = [math.ceil(i) for i in botleft]

        # Get indexes at top right
        topright = [
            botleft[0] + rect.get_width(),
            botleft[1] + rect.get_height(),
        ]
        topright = [math.ceil(i) for i in topright]

        # Get image rows
        ys = [botleft[1], topright[1]]
        xs = [botleft[0], topright[0]]
        sample = image[min(ys):max(ys),min(xs):max(xs), :]
        print(sample.shape)

        df = pandas.concat(
            [df, dataBox2df(sample, bandnames)]
        ).reset_index(drop=True)

    df['class'] = surface_class 

    return df


def generateTree(class_data):
    # Create full training dataframe
    class_df = pandas.DataFrame()
    for df in class_data.values():
        class_df = class_df.append(df)
    class_df = class_df.dropna(how='any')

    # Initialize classifier
    clf = DecisionTreeClassifier(
        random_state=0, 
        max_depth=100
    )

    feature_cols = [b for b in bandnames]
    x_train, x_test, y_train, y_test = train_test_split(
        class_df[feature_cols], 
        class_df['class'], 
        test_size=0.1, 
        random_state=1
    )

    clf = clf.fit(
        x_train,
        y_train
    )

    y_pred = clf.predict(x_test)
    print("Accuracy:", metrics.accuracy_score(y_test, y_pred))

    return clf


scene_pattern = '/Users/greenberg/Documents/PHD/Projects/Chapter2/GIS/Tarim/migration/2019/raw/*.tif'
fps = glob.glob(scene_pattern)

bandnames = [
    'cblue',
    'blue',
    'green',
    'red',
    'nir',
    'swir1',
    'swir2',
]

classes = [
    'water',
    'other'
]
classes_n = [
    1,
    2,
]

class_data = {}
for idx, fp in enumerate(fps):
    ds = rasterio.open(fp)
    class_image = np.moveaxis(ds.read(), 0, -1)

    if idx == 0:
        print('now picking water')
        water_df = generateTrainingData(
            class_image, 1, bandnames
        )
        print('now picking non-water')
        nonwater_df = generateTrainingData(
            class_image, 0, bandnames
        )

    else:
        print('now picking water')
        water_df = water_df.append(
            generateTrainingData(class_image, 1, bandnames)
        )

        print('now picking non-water')
        nonwater_df = nonwater_df.append(
            generateTrainingData(class_image, 0, bandnames)
        )


class_data['water'] = water_df
class_data['other'] = nonwater_df

clf = generateTree(class_data)
dump(clf, 'clf_2019.joblib') 
clf = load('clf_2019.joblib')

scene_pattern = '/Users/greenberg/Documents/PHD/Projects/Chapter2/GIS/Tarim/migration/2019/raw/*.tif'
fps = glob.glob(scene_pattern)
for jdx, fp in enumerate(fps):
    print('Running: ')
    print(fp)
    print()
    ds = rasterio.open(fp)
    class_image = np.moveaxis(ds.read(), 0, -1)

    class_image[class_image == -9999] = np.nan
    image = class_image
    new_shape = (image.shape[0] * image.shape[1], image.shape[2])
    img_as_array = image[:, :, :].reshape(new_shape)

    predictions = np.empty([img_as_array.shape[0]])
    predictions[:] = None
    for i, row in enumerate(img_as_array):
        if len(row[~np.isnan(row)]) == 7:
            predictions[i] = clf.predict(row.reshape(1, len(bandnames)))[0]

    # Reshape our classification map
    class_prediction = predictions.reshape(image[:, :, 0].shape)

    struct = ndimage.generate_binary_structure(2, 2)

    class_prediction = ndimage.binary_closing(
        ndimage.median_filter(class_prediction,size=2), 
        structure=struct
    )

    ds = rasterio.open(fp)
    dsmeta = ds.meta
    dsmeta.update(
        width=class_prediction.shape[1],
        height=class_prediction.shape[0],
        count=1,
    )

    # Save file
    out_root = '/Users/greenberg/Documents/PHD/Projects/Chapter2/GIS/Tarim/migration/2019/mask'
    image_name = fp.split('/')[-1]
    images = image_name.split('_')
    images[-1] = 'mask.tif'
    image_name = '_'.join(images)
    if not os.path.isdir(out_root):
        os.mkdir(out_root)

    out_path = os.path.join(out_root, image_name)
    with rasterio.open(out_path, 'w', **dsmeta) as dst:
        dst.write(class_prediction.astype(rasterio.float32), 1)


# rgb = class_image[:, :, [3, 2, 1]]
# rgb[rgb == -9999] = np.nan
# bottom = np.nanpercentile(rgb, 5, axis=(0,1))
# top = np.nanpercentile(rgb, 95, axis=(0,1))
# rgb = np.clip(rgb, bottom, top)
# rgb = (
#     rgb-np.nanmin(rgb, axis=(0,1))
# ) / (
#     np.nanmax(rgb, axis=(0,1)) 
#     - np.nanmin(rgb, axis=(0,1))
# )
# 
# 
# test = ndimage.binary_erosion(
#     binary_fill_holes(ndimage.binary_dilation(
#         ndimage.median_filter(class_prediction, size=2), 
#         structure=struct
#     )),
#     structure=struct
# )
# 
# test = ndimage.binary_closing(
#     ndimage.median_filter(class_precition,size=2), 
#     structure=struct
# )
# 
# bf = ndimage.distance_transform_bf(class_prediction)
# bf = bf > 2
# plt.imshow(bf)
# plt.show()
# 
# fig, axs = plt.subplots(3, 1, sharey=True, sharex=True)
# axs[0].imshow(rgb)
# axs[1].imshow(class_prediction)
# axs[2].imshow(test)
# plt.show()


#    out_file = '/home/greenberg/ExtraSpace/PhD/JPL/DataFiles/for_cedric/classifications'
#    for fp in fps:
#        print(fp)
#        outfile, classnums, classlist = Preclassify(fp, out_file)
