import os
import cv2
import torch
import config
import numpy as np


def obtain_dictionaries():
	files = [f for f in os.listdir(os.path.join(config.data_path, 'GT')) if f.endswith('.txt')]

	vocab = list()
	for single_file in files:
		with open(os.path.join(config.data_path, 'GT', single_file)) as f:
			fin = f.readlines()[0].split()
			vocab.extend(fin)
		vocab = list(set(vocab))
	vocab = sorted(vocab)


	w2i = {vocab[u]:u for u in range(len(vocab))}
	i2w = {i:w for w,i in w2i.items()}

	return w2i, i2w

def new_obtain_dictionaries(type, name):
	files = [f for f in os.listdir(os.path.join(config.DDBB_path, 'lists', name)) if f.endswith('.txt')]

	vocab = list()
	for single_file in files:
		with open(os.path.join(config.DDBB_path, 'lists', name, single_file)) as f:
			fin = f.readlines()
			for x in fin:
				token = x.split()
				vocab.extend(token)
		vocab = list(set(vocab))
	vocab = sorted(vocab)


	w2i = {vocab[u]:u for u in range(len(vocab))}
	i2w = {i:w for w,i in w2i.items()}

	return w2i, i2w

"""Image shape adaptation"""
def adapt_images_aspect_ratio(img, new_height, keep_aspect_ratio = True):
	#Retrieving dimesions of the input image:
	height, width = img.shape

	if new_height == -1: #No aspect ratio
		new_height = height

	if keep_aspect_ratio == True:
		new_width = int(new_height*width/float(height))

	#In terms of height, we rescale the image:
	out_img = cv2.resize(img,(new_width, new_height), interpolation = cv2.INTER_AREA)


	return out_img, new_width

def read_image(path_to_image):
	file_img = cv2.imread(path_to_image)

	return file_img

def read_gt(path_to_gt):
	with open(path_to_gt) as f:
		GT = f.readlines()[0].split()

	return GT

def load_batch_data(w2i, files, img_height, type, name):
	img_batch = list()
	gt_batch = list()
	input_length = list()
	label_length = list()

	for single_file in files:
		# Image:
		###-Image processing:
		file_img = read_image(os.path.join(config.DDBB_path, type, single_file + '.png'))

		init_img = (255. - cv2.cvtColor(file_img, cv2.COLOR_BGR2GRAY))/255
		temp_img, init_width = adapt_images_aspect_ratio(img = init_img, new_height = img_height)
		
		if len(temp_img.shape) == 2: temp_img = np.expand_dims(temp_img, -1)
		temp_img = np.transpose(temp_img, (2, 0, 1))
		
		
		img_batch.append(temp_img)

		###-Image width
		input_length.append(init_width)

		# GT:
		###-Saving GT:
		gt_batch.append([w2i[u] for u in read_gt(os.path.join('Temp', 'GT', single_file.split('/')[1] + '.txt'))])
		
		###-Label length:
		label_length.append(len(gt_batch[-1]))	

	# Additional vectors:
	### Image length:
	max_length = max(input_length)
	for Y_it in range(len(img_batch)):
		ref_shape = img_batch[Y_it].shape
		img_batch[Y_it] = np.concatenate((img_batch[Y_it],  np.zeros(shape=(ref_shape[0], ref_shape[1], max_length-ref_shape[2]))), axis=2)

	input_length = [u//16 for u in input_length]

	### GT length:
	max_length = max(label_length)
	for single_seq in gt_batch:
		single_seq.extend([-1]*(max_length - len(single_seq)))

	return img_batch, gt_batch, input_length, label_length


def data_generator(w2i, type, name, rate, img_height = 50, partition = 'train'):
	# Listing train files:
	with open(os.path.join('Temp', 'Folds', partition + '.txt')) as f:
		files = list(map(str.strip, f.readlines()))
	
	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

	idx = 0
	while True:

		files_list = list()
		for _ in range(config.batch_size):		
			files_list.append(files[idx])
			idx = idx + 1 if idx < len(files)-1 else 0

		img_batch, gt_batch, input_length, label_length = load_batch_data(w2i, files_list, img_height, type, name)

		yield torch.from_numpy(np.array(img_batch)).to(device), torch.from_numpy(np.array(gt_batch)).to(device), torch.from_numpy(np.array(input_length)).to(device), torch.from_numpy(np.array(label_length)).to(device)

def create_fold(type, name, partition, rate):
	with open(os.path.join(config.folds_path, type, name, partition + '.txt')) as f:
		files = list(map(str.strip, f.readlines()))

	lim_files = (len(files) * int(rate)) // 100

	new_files = files[:lim_files]
	res_files = files[lim_files:]

	f  = open(os.path.join(config.folds_path, type, name, 'rate', partition + ".txt"), "a")
	ff = open(os.path.join('Temp', 'Folds', partition + ".txt"), "a")
	for x in new_files:
		f.write(x + "\n")
		ff.write(os.path.join(name, x) + '\n')
	f.close()
	ff.close()

	f = open(os.path.join(config.folds_path, type, name, 'rate', 'res_' + partition + ".txt"), "a")
	ff = open(os.path.join('Temp', 'Folds', 'res_' + partition + ".txt"), "a")
	for x in res_files:
		f.write(x + "\n")
		ff.write(os.path.join(name, x) + '\n')
	f.close()
	ff.close()

if __name__ == '__main__':
	w2i, i2w = obtain_dictionaries()
	data_gen = data_generator(w2i = w2i, img_height = config.img_height)

	img, seq, img_len, seq_len = next(data_gen)
	# b0, b1 = batches
	print(w2i)
	print("----------")
	print(i2w)
	print("hello")


