import torch
import imageio
import numpy as np
import os
import datetime
import skimage.color as sc

import matplotlib

matplotlib.use('Agg')
from matplotlib import pyplot as plt


class Logger:
    def __init__(self, args):
        self.args = args
        self.psnr_log = torch.Tensor()
        self.loss_log = torch.Tensor()

        if args.load == '.':
            if args.save == '.':
                args.save = datetime.datetime.now().strftime('%Y%m%d_%H:%M')
            self.dir = args.experiment_dir + args.save
        else:
            self.dir = args.experiment_dir + args.load
            if not os.path.exists(self.dir):
                args.load = '.'
            else:
                self.loss_log = torch.load(self.dir + '/loss_log.pt')
                self.loss_log = self.loss_log.squeeze(1)
                self.psnr_log = torch.load(self.dir + '/psnr_log.pt')
                print('Continue from epoch {}...'.format(str(50)))

        #if not os.path.exists(self.dir):
        #    os.makedirs(self.dir)
        #    if not os.path.exists(self.dir + '/model'):
        #        os.makedirs(self.dir + '/model')
        #if not os.path.exists(self.dir + '/result/' + self.args.data_test):
        #    print("Creating dir for saving images...", self.dir + '/result/' + self.args.data_test)
        #    os.makedirs(self.dir + '/result/' + self.args.data_test)

        print('Save Path : {}'.format(self.dir))

        open_type = 'a' if os.path.exists(self.dir + '/log.txt') else 'w'
        #self.log_file = open(self.dir + '/log.txt', open_type)
        #with open(self.dir + '/config.txt', open_type) as f:
        #    f.write('From epoch {}...'.format(len(self.psnr_log)) + '\n\n')
        #    for arg in vars(args):
        #        f.write('{}: {}\n'.format(arg, getattr(args, arg)))
        #    f.write('\n')

    def write_log(self, log):
        print(log)
        #self.log_file.write(log + '\n')

    def save(self, trainer, epoch, is_best):
        trainer.model.save(self.dir, epoch, is_best)
        torch.save(self.psnr_log, os.path.join(self.dir, 'psnr_log.pt'))
        torch.save(trainer.optimizer.state_dict(), os.path.join(self.dir, 'optimizer.pt'))
        trainer.loss.save(self.dir)
        trainer.loss.plot_loss(self.dir, epoch)
        self.plot_psnr_log(epoch)

    def save_kernel(self, kernel, kernel_in, filename):
        kernel_in = kernel_in / torch.max(kernel_in) * 255
        kernel_in = np.transpose(kernel_in.cpu().numpy(), (1, 2, 0)).astype(np.uint8)
        kernel_in_save = np.zeros((kernel_in.shape[0], kernel_in.shape[1], 3))

        kernel = kernel * 255
        kernel1 = kernel / torch.max(kernel) * 255
        kernel = np.transpose(kernel.cpu().numpy(), (1, 2, 0)).astype(np.uint8)
        kernel1 = np.transpose(kernel1.cpu().numpy(), (1, 2, 0)).astype(np.uint8)
        kernel_save = np.zeros((kernel.shape[0], kernel.shape[1], 3))
        kernel_save1 = np.zeros((kernel1.shape[0], kernel1.shape[1], 3))
        for i in range(3):
            kernel_save[:, :, i:i+1] = kernel
            kernel_save1[:, :, i:i+1] = kernel1
            kernel_in_save[:, :, i:i+1] = kernel_in

        # kernel_save /= np.max(kernel_save)
        f = filename.split('.')
        dirname = '{}/result/{}/{}'.format(self.dir, self.args.data_test, f[0])
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        filename = '{}/{}'.format(dirname, f[1])
        imageio.imwrite(os.path.join('{}_kernel.png'.format(filename)), kernel_save.astype(np.uint8))
        imageio.imwrite(os.path.join('{}_kernel1.png'.format(filename)), kernel_save1.astype(np.uint8))
        imageio.imwrite(os.path.join('{}_kernel_in.png'.format(filename)), kernel_in_save.astype(np.uint8))

    def save_train_images(self, save_list, epoch, batch):
        if self.args.model == 'DBVSR':
            dirname = '{}/result/{}/train'.format(self.dir, self.args.data_test)
            if not os.path.exists(dirname):
                os.mkdir(dirname)
            filename = '{}/{}epoch_{}iters'.format(dirname, batch, epoch)
            postfix = ['train_map']
        else:
            raise NotImplementedError('Model [{:s}] is not found'.format(self.args.model))
        for img, post in zip(save_list, postfix):
            img = img[0].data
            img = np.transpose(img.cpu().numpy(), (1, 2, 0)).astype(np.uint8)
            if img.shape[2] == 1:
                img = img.squeeze(axis=2)
            elif img.shape[2] == 3 and self.args.n_colors == 1:
                img = sc.ycbcr2rgb(img.astype('float')).clip(0, 1)
                img = (255 * img).round().astype('uint8')
            imageio.imwrite('{}_{}.png'.format(filename, post), img)


    def save_images(self, filename, save_list, testset):
        if self.args.model == 'DBVSR':
            f = filename.split('.')
            dirname = '{}/result/{}/{}/{}'.format(self.dir, self.args.data_test, testset, f[0])
            #if not os.path.exists(dirname):
                #os.makedirs(dirname)
            filename = '{}/{}'.format(dirname, f[1])
            postfix = ['dbvsr']

        elif self.args.model == 'baseline_lr':
            f = filename.split('.')
            dirname = '{}/result/{}/{}/{}'.format(self.dir, self.args.data_test, testset, f[0])
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            filename = '{}/{}'.format(dirname, f[1])
            postfix = ['bl']

        elif self.args.model == 'baseline_hr':
            f = filename.split('.')
            dirname = '{}/result/{}/{}/{}'.format(self.dir, self.args.data_test, testset, f[0])
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            filename = '{}/{}'.format(dirname, f[1])
            postfix = ['bh']
        else:
            raise NotImplementedError('Model [{:s}] is not found'.format(self.args.model))
        for img, post in zip(save_list, postfix):
            img = img[0].data
            img = np.transpose(img.cpu().numpy(), (1, 2, 0)).astype(np.uint8)
            if img.shape[2] == 1:
                img = img.squeeze(axis=2)
            elif img.shape[2] == 3 and self.args.n_colors == 1:
                img = sc.ycbcr2rgb(img.astype('float')).clip(0, 1)
                img = (255 * img).round().astype('uint8')
            words = list(filename.split('//'))
            last = words[-1]
            from pathlib import Path
            words = list(last.split('/'))
            direct = ""
            for word in words[:-1]:
                direct += "/" + word
            Path(direct).mkdir(parents=True, exist_ok=True)
            imageio.imwrite(f"/{last}.png", img)

    def start_log(self, train=True):
        if train:
            self.loss_log = torch.cat((self.loss_log, torch.zeros(1)))
        else:
            self.psnr_log = torch.cat((self.psnr_log, torch.zeros(1)))

    def report_log(self, item, train=True):
        if train:
            self.loss_log[-1] += item
        else:
            self.psnr_log[-1] += item

    def end_log(self, n_div, train=True):
        if train:
            self.loss_log[-1].div_(n_div)
        else:
            self.psnr_log[-1].div_(n_div)

    def plot_loss_log(self, epoch):
        axis = np.linspace(1, epoch, epoch)
        fig = plt.figure()
        plt.title('Loss Graph')
        plt.plot(axis, self.loss_log.numpy())
        plt.legend()
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.grid(True)
        plt.savefig(os.path.join(self.dir, 'loss.pdf'))
        plt.close(fig)

    def plot_psnr_log(self, epoch):
        axis = np.linspace(1, epoch, epoch)
        fig = plt.figure()
        plt.title('PSNR Graph')
        plt.plot(axis, self.psnr_log.numpy())
        plt.legend()
        plt.xlabel('Epochs')
        plt.ylabel('PSNR')
        plt.grid(True)
        plt.savefig(os.path.join(self.dir, 'psnr.pdf'))
        plt.close(fig)

    def done(self):
        pass#self.log_file.close()
