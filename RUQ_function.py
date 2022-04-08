import numpy as np
from scipy.optimize import curve_fit
import scipy
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import LinearLocator, FuncFormatter, FormatStrFormatter
from copy import copy
import os
import pickle

path = 'figures/'
if not os.path.exists(path):
    os.makedirs(path)
    
class plotinfo:
    def __init__(self, n_realization, Kg, Lx, Ly, lambda_x, lambda_y, 
                 source_xl, source_xu, source_yl, source_yu, 
                 target_xl, target_xu, target_yl, target_yu,
                 mcl, observation_wells, dt):
        
        self.n_realization = n_realization
        self.Kg = Kg
        self.Lx = Lx
        self.Ly = Ly
        self.lambda_x = lambda_x 
        self.lambda_y = lambda_y
        self.source_xl = source_xl 
        self.source_xu = source_xu
        self.source_yl = source_yl 
        self.source_yu = source_yu
        self.target_xl = target_xl
        self.target_xu = target_xu
        self.target_yl = target_yl
        self.target_yu = target_yu
        self.mcl = mcl
        self.observation_wells = np.asarray(observation_wells)
        self.dt = dt
        
        self.kfields = np.load('data/Kfileds_Hydrogen.npy')
        self.kmax = np.ceil(np.max(self.kfields))
        self.kmin = np.floor(np.min(self.kfields))
        

    def logkfield(self, filename, real_n):
        kfield = self.kfields[real_n]
        fig, ax = plt.subplots(figsize=(7,5))
        img = ax.imshow(kfield, cmap='jet', extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0], 
                        vmin=self.kmin, vmax=self.kmax)
        rectangle1 = plt.Rectangle((self.source_xl/self.lambda_x,self.source_yl/self.lambda_y), 
                                  (self.source_xu-self.source_xl)/self.lambda_x, 
                                  (self.source_yu-self.source_yl)/self.lambda_y, 
                                  fc='k', fill=None, linewidth=1.5)
        plt.gca().add_patch(rectangle1)
        plt.text(self.source_xl/self.lambda_x, (self.source_yl-self.lambda_y)/self.lambda_y, r'source', fontsize=15, color='k')
        
        rectangle2 = plt.Rectangle((self.target_xl/self.lambda_x,self.target_yl/self.lambda_y), 
                                  (self.target_xu-self.target_xl)/self.lambda_x, 
                                  (self.target_yu-self.target_yl)/self.lambda_y, 
                                  fc='k', fill=None, linewidth=1.5)
        plt.gca().add_patch(rectangle2)       
        plt.text(self.target_xl/self.lambda_x, (self.target_yl-self.lambda_y)/self.lambda_y, r'target', fontsize=15, color='k')

        ax.scatter(self.observation_wells.T[0]/self.lambda_x, self.observation_wells.T[1]/self.lambda_y, 
                   color='k', marker='^' ,s=50, label='observation well')
        
        cbar = ax.figure.colorbar(img, ax=ax, fraction=0.041, pad=0.04)
        cbar.ax.tick_params(labelsize=14)
        cbar.ax.set_ylabel(r'$log~K$', fontsize=25, fontname='Arial', labelpad=10)
        ax.xaxis.set_major_locator(LinearLocator(5))
        ax.xaxis.set_minor_locator(LinearLocator(21))
        ax.yaxis.set_major_locator(LinearLocator(5))
        ax.yaxis.set_minor_locator(LinearLocator(21))

        plt.xlim(0,self.Lx/self.lambda_x)
        plt.ylim(0,self.Ly/self.lambda_y)
        plt.xticks(fontsize=15, fontname='Arial')
        plt.yticks(fontsize=15, fontname='Arial')
        plt.xlabel(r'$x~/~\lambda_x$', fontsize=25, fontname='Arial', labelpad=5)
        plt.ylabel(r'$y~/~\lambda_y$', fontsize=25, fontname='Arial', labelpad=5)

        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.savefig(f'figures/{filename}.png',dpi=100, bbox_inches='tight')
        plt.show()


    def cfield_postprocessing(self):
        cfield_all = []
        for i in range(self.n_realization):
            cfield_all.append(np.load(f'data/cfields/cfield_{i}.npy'))
        cfield_all = np.asarray(cfield_all)
        np.save(f'data/cfields/cfield_all.npy', cfield_all)
        cfield_ave = cfield_all.mean(axis=0)
        np.save(f'data/cfields/cfield_ensemble.npy', cfield_ave)
        cfield_var = cfield_all.var(axis=0)
        np.save(f'data/cfields/cfield_ensemble_v.npy', cfield_var)
        
    def cfield(self, filename, real_n, time_index, plume_edge, max_conc):
        field_c = np.load(f'data/cfields/cfield_{real_n}.npy')
        risk_var = np.load('data/cfields/cfield_ensemble_v.npy', )
        if not real_n == 'ensemble':
            kfield = self.kfields[real_n]
            alpha_v = 0.7
            maxconc = pickle.load(open(f'data/referencepoints/maxconc_{real_n}.pkl', 'rb'))
            edge = pickle.load(open(f'data/referencepoints/edge_{real_n}.pkl', 'rb'))
            ylabel = r'$c$'
        else:
            alpha_v = 1
            ylabel = r'$\left< c \right>$'
            
        c0 = field_c[0].max()

        for i in time_index:
            fig, ax = plt.subplots(figsize=(7,5))
            cmap = copy(plt.get_cmap('Greens'))
            def fmt(x, pos):
                a, b = '{:.0e}'.format(x).split('e')
                b = int(b)
                return r'${} \times 10^{{{}}}$'.format(a, b)
            if not real_n == 'ensemble':
                img = ax.imshow(kfield, cmap='jet', extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0], 
                                vmin=self.kmin, vmax=self.kmax)
            img = ax.imshow(field_c[i,:,:-1]/c0, cmap=cmap, 
                            extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0], vmin=0, vmax=1e0, alpha=alpha_v)
            cbar = ax.figure.colorbar(img, ax=ax, fraction=0.041, pad=0.04, format=FuncFormatter(fmt))
            cbar.ax.tick_params(labelsize=14)
            cbar.ax.set_ylabel(ylabel, fontsize=25, fontname='Arial', labelpad=10)
            cbar.solids.set_edgecolor("face")
            ax.scatter(self.observation_wells.T[0]/self.lambda_x, self.observation_wells.T[1]/self.lambda_y, 
                       color='k', marker='^' ,s=50)            
            
            if not real_n == 'ensemble':
                if plume_edge:
                    edge_index = edge['tstep']//self.dt == i
                    edge_indexes = edge['tstep']//self.dt <= i

                    ax.scatter(edge['x_coord'][edge_index]/self.lambda_x, edge['y_coord'][edge_index]/self.lambda_y,
                               s=80, c='b', marker='X', linewidths=.01, alpha=0.8, label='plume edge')
                    ax.plot(edge['x_coord'][edge_indexes]/self.lambda_x, edge['y_coord'][edge_indexes]/self.lambda_y,
                            c='b', linestyle=':', alpha=0.8)
                    plt.legend(loc=2, fontsize=12)

                if max_conc:
                    maxconc_index = maxconc['tstep']//self.dt == i
                    maxconc_indexes = maxconc['tstep']//self.dt <= i

                    ax.scatter(maxconc['x_coord'][maxconc_index]/self.lambda_x, maxconc['y_coord'][maxconc_index]/self.lambda_y,
                               s=80, c='r', marker='X', linewidths=.01, alpha=0.8, label='conc. max')
                    ax.scatter(maxconc['x_coord'][maxconc_indexes]/self.lambda_x, maxconc['y_coord'][maxconc_indexes]/self.lambda_y,
                               s=30, c='r', marker='X', linewidths=.01, alpha=0.5)
                    plt.legend(loc=2, fontsize=12)

            ax.xaxis.set_major_locator(LinearLocator(5))
            ax.xaxis.set_minor_locator(LinearLocator(21))
            ax.yaxis.set_major_locator(LinearLocator(5))
            ax.yaxis.set_minor_locator(LinearLocator(21))

            rectangle2 = plt.Rectangle((self.target_xl/self.lambda_x,self.target_yl/self.lambda_y), 
                                      (self.target_xu-self.target_xl)/self.lambda_x, 
                                      (self.target_yu-self.target_yl)/self.lambda_y, 
                                      fc='k', fill=None, linewidth=1.5)
            plt.gca().add_patch(rectangle2)       

            plt.xlim(0,self.Lx/self.lambda_x)
            plt.ylim(0,self.Ly/self.lambda_y)
            plt.xticks(fontsize=15, fontname='Arial')
            plt.yticks(fontsize=15, fontname='Arial')
            plt.xlabel(r'$x~/~\lambda_x$', fontsize=25, fontname='Arial', labelpad=5)
            plt.ylabel(r'$y~/~\lambda_y$', fontsize=25, fontname='Arial', labelpad=5)

            plt.text(5/self.lambda_x, 5/self.lambda_y, f'$t={i*self.dt}$', fontsize=15, color='k')
            plt.tight_layout()
            plt.savefig(f'figures/{filename}_{i}.png',dpi=200, bbox_inches='tight')
            
            if real_n == 'ensemble':
                fig, ax = plt.subplots(figsize=(7,5))
                cmap = copy(plt.get_cmap('Purples'))
                ylabel = r'$\sigma^2_{c}$'
                def fmt(x, pos):
                    a, b = '{:.0e}'.format(x).split('e')
                    b = int(b)
                    return r'${} \times 10^{{{}}}$'.format(a, b)
                img = ax.imshow(risk_var[i,:,:-1], cmap=cmap, 
                                extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0], 
                                vmin=0, vmax=np.max(risk_var[i,:,:-self.lambda_x]), alpha=alpha_v)
                cbar = ax.figure.colorbar(img, ax=ax, fraction=0.041, pad=0.04, format=FuncFormatter(fmt))
                cbar.ax.tick_params(labelsize=14)
                cbar.ax.set_ylabel(ylabel, fontsize=25, fontname='Arial', labelpad=10)
                cbar.solids.set_edgecolor("face")
                ax.scatter(self.observation_wells.T[0]/self.lambda_x, self.observation_wells.T[1]/self.lambda_y, 
                           color='k', marker='^' ,s=50)

                ax.xaxis.set_major_locator(LinearLocator(5))
                ax.xaxis.set_minor_locator(LinearLocator(21))
                ax.yaxis.set_major_locator(LinearLocator(5))
                ax.yaxis.set_minor_locator(LinearLocator(21))

                rectangle2 = plt.Rectangle((self.target_xl/self.lambda_x,self.target_yl/self.lambda_y), 
                                          (self.target_xu-self.target_xl)/self.lambda_x, 
                                          (self.target_yu-self.target_yl)/self.lambda_y, 
                                          fc='k', fill=None, linewidth=1.5)
                plt.gca().add_patch(rectangle2)       

                plt.xlim(0,self.Lx/self.lambda_x)
                plt.ylim(0,self.Ly/self.lambda_y)
                plt.xticks(fontsize=15, fontname='Arial')
                plt.yticks(fontsize=15, fontname='Arial')
                plt.xlabel(r'$x~/~\lambda_x$', fontsize=25, fontname='Arial', labelpad=5)
                plt.ylabel(r'$y~/~\lambda_y$', fontsize=25, fontname='Arial', labelpad=5)

                plt.text(5/self.lambda_x, 5/self.lambda_y, f'$t={i*self.dt}$', fontsize=15, color='k')
                plt.tight_layout()
                plt.savefig(f'figures/{filename}_v_{i}.png',dpi=200, bbox_inches='tight')            
                ylabel = r'$\left< c \right>$'
            

    def rrfield_postprocessing(self):
        cfield_all = np.load('data/cfields/cfield_all.npy')
        reliability_field = np.zeros(cfield_all.shape)
        resilience_field = np.zeros((self.n_realization, self.Ly, self.Lx))
        for real_n in range(self.n_realization):
            field_c = cfield_all[real_n]
            c0 = field_c[0].max()
            reliability_field[real_n] = np.where(field_c >= (self.mcl*c0), 1, 0)
            resilience_field[real_n] = np.sum(reliability_field[real_n], axis=0)*self.dt
        risk_ensemble = reliability_field.mean(axis=0)
        risk_var = reliability_field.var(axis=0)
        np.save('data/reliability_field', reliability_field)
        np.save('data/risk_ensemble', risk_ensemble)
        np.save('data/risk_ensemble_v', risk_var)
        np.save('data/resilience_field', resilience_field)
            
    def riskfield(self, filename, real_n, time_index):
        if not real_n == 'ensemble':
            kfield = self.kfields[real_n]
            alpha_v = 0.7
            field_c = np.load(f'data/cfields/cfield_{real_n}.npy')
            field_maxrisk = np.zeros(field_c.shape)
            c0 = field_c[0].max()
            field_maxrisk = np.where(field_c >= (self.mcl*c0), field_c/(self.mcl*c0), 0)

            for i in time_index:
                fig, ax = plt.subplots(figsize=(7,5))
                cmap = copy(plt.get_cmap('Reds'))
                def fmt(x, pos):
                    a, b = '{:.0e}'.format(x).split('e')
                    b = int(b)
                    return r'${} \times 10^{{{}}}$'.format(a, b)

                if not real_n == 'ensemble':
                    img = ax.imshow(kfield, cmap='jet', extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0],
                                    vmin=self.kmin, vmax=self.kmax)
                img = ax.imshow(field_maxrisk[i], cmap=cmap, extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0], 
                                vmin=1, vmax=np.ceil(field_maxrisk[i][:,:-8].max()), alpha=alpha_v)
                cbar = ax.figure.colorbar(img, ax=ax, fraction=0.041, pad=0.04, format=FuncFormatter(fmt))
                cbar.ax.tick_params(labelsize=14)
                cbar.ax.set_ylabel(r'$\rm{max}$ $c~/~\rm{mcl}$', fontsize=25, fontname='Arial', labelpad=10)
                cbar.solids.set_edgecolor("face")
                ax.scatter(self.observation_wells.T[0]/self.lambda_x, self.observation_wells.T[1]/self.lambda_y, 
                           color='k', marker='^' ,s=50)                  

                ax.xaxis.set_major_locator(LinearLocator(5))
                ax.xaxis.set_minor_locator(LinearLocator(21))
                ax.yaxis.set_major_locator(LinearLocator(5))
                ax.yaxis.set_minor_locator(LinearLocator(21))

                rectangle2 = plt.Rectangle((self.target_xl/self.lambda_x,self.target_yl/self.lambda_y), 
                                          (self.target_xu-self.target_xl)/self.lambda_x, 
                                          (self.target_yu-self.target_yl)/self.lambda_y, 
                                          fc='k', fill=None, linewidth=1.5)
                plt.gca().add_patch(rectangle2)            

                plt.xlim(0,self.Lx/self.lambda_x)
                plt.ylim(0,self.Ly/self.lambda_y)
                plt.xticks(fontsize=15, fontname='Arial')
                plt.yticks(fontsize=15, fontname='Arial')
                plt.xlabel(r'$x~/~\lambda_x$', fontsize=25, fontname='Arial', labelpad=5)
                plt.ylabel(r'$y~/~\lambda_y$', fontsize=25, fontname='Arial', labelpad=5)
                plt.text(5/self.lambda_x, 5/self.lambda_y, f'$t={i*self.dt}$', fontsize=15, color='k')
                plt.tight_layout()
                plt.savefig(f'figures/{filename}_{i}.png',dpi=200, bbox_inches='tight')            
        else:
            alpha_v = 1
            field_maxrisk = np.load(f'data/risk_ensemble.npy')
            risk_var = np.load('data/risk_ensemble_v.npy', )
            
            for i in time_index:
                fig, ax = plt.subplots(figsize=(7,5))
                cmap = copy(plt.get_cmap('Reds'))
                def fmt(x, pos):
                    a, b = '{:.0e}'.format(x).split('e')
                    b = int(b)
                    return r'${} \times 10^{{{}}}$'.format(a, b)

                img = ax.imshow(field_maxrisk[i], cmap=cmap, extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0], 
                                vmin=0, vmax=1, alpha=alpha_v)
                cbar = ax.figure.colorbar(img, ax=ax, fraction=0.041, pad=0.04, format=FuncFormatter(fmt))
                cbar.ax.tick_params(labelsize=14)
                cbar.ax.set_ylabel(r'$\left<\xi\right>$', fontsize=25, fontname='Arial', labelpad=10)
                cbar.solids.set_edgecolor("face")
                ax.scatter(self.observation_wells.T[0]/self.lambda_x, self.observation_wells.T[1]/self.lambda_y, 
                           color='k', marker='^' ,s=50)            
                

                ax.xaxis.set_major_locator(LinearLocator(5))
                ax.xaxis.set_minor_locator(LinearLocator(21))
                ax.yaxis.set_major_locator(LinearLocator(5))
                ax.yaxis.set_minor_locator(LinearLocator(21))

                rectangle2 = plt.Rectangle((self.target_xl/self.lambda_x,self.target_yl/self.lambda_y), 
                                          (self.target_xu-self.target_xl)/self.lambda_x, 
                                          (self.target_yu-self.target_yl)/self.lambda_y, 
                                          fc='k', fill=None, linewidth=1.5)
                plt.gca().add_patch(rectangle2)            

                plt.xlim(0,self.Lx/self.lambda_x)
                plt.ylim(0,self.Ly/self.lambda_y)
                plt.xticks(fontsize=15, fontname='Arial')
                plt.yticks(fontsize=15, fontname='Arial')
                plt.xlabel(r'$x~/~\lambda_x$', fontsize=25, fontname='Arial', labelpad=5)
                plt.ylabel(r'$y~/~\lambda_y$', fontsize=25, fontname='Arial', labelpad=5)
                plt.text(5/self.lambda_x, 5/self.lambda_y, f'$t={i*self.dt}$', fontsize=15, color='k')
                plt.tight_layout()
                plt.savefig(f'figures/{filename}_{i}.png',dpi=200, bbox_inches='tight')
                
                fig, ax = plt.subplots(figsize=(7,5))
                cmap = copy(plt.get_cmap('Purples'))
                def fmt(x, pos):
                    a, b = '{:.0e}'.format(x).split('e')
                    b = int(b)
                    return r'${} \times 10^{{{}}}$'.format(a, b)

                img = ax.imshow(risk_var[i], cmap=cmap, extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0], 
                                vmin=0, vmax=np.max(risk_var[i][:,:-self.lambda_x]), alpha=alpha_v)
                   
                cbar = ax.figure.colorbar(img, ax=ax, fraction=0.041, pad=0.04, format=FuncFormatter(fmt))
                cbar.ax.tick_params(labelsize=14)
                cbar.ax.set_ylabel(r'$\sigma^2_{\xi}$', fontsize=25, fontname='Arial', labelpad=10)
                cbar.solids.set_edgecolor("face")
                ax.scatter(self.observation_wells.T[0]/self.lambda_x, self.observation_wells.T[1]/self.lambda_y, 
                           color='k', marker='^' ,s=50)            

                ax.xaxis.set_major_locator(LinearLocator(5))
                ax.xaxis.set_minor_locator(LinearLocator(21))
                ax.yaxis.set_major_locator(LinearLocator(5))
                ax.yaxis.set_minor_locator(LinearLocator(21))

                rectangle2 = plt.Rectangle((self.target_xl/self.lambda_x,self.target_yl/self.lambda_y), 
                                          (self.target_xu-self.target_xl)/self.lambda_x, 
                                          (self.target_yu-self.target_yl)/self.lambda_y, 
                                          fc='k', fill=None, linewidth=1.5)
                plt.gca().add_patch(rectangle2)            

                plt.xlim(0,self.Lx/self.lambda_x)
                plt.ylim(0,self.Ly/self.lambda_y)
                plt.xticks(fontsize=15, fontname='Arial')
                plt.yticks(fontsize=15, fontname='Arial')
                plt.xlabel(r'$x~/~\lambda_x$', fontsize=25, fontname='Arial', labelpad=5)
                plt.ylabel(r'$y~/~\lambda_y$', fontsize=25, fontname='Arial', labelpad=5)
                plt.text(5/self.lambda_x, 5/self.lambda_y, f'$t={i*self.dt}$', fontsize=15, color='k')
                plt.tight_layout()
                plt.savefig(f'figures/{filename}_v_{i}.png',dpi=200, bbox_inches='tight')

        
    def resiliencefield(self, filename, real_n):        
        if not real_n == 'ensemble':
            kfield = self.kfields[real_n]
            field_resilience = np.load(f'data/resilience_field.npy')[real_n]
            alpha_v = 0.7
        else:
            field_resilience = np.load(f'data/resilience_field.npy').mean(axis=0)
            field_resilience_var = np.load(f'data/resilience_field.npy').var(axis=0)
            alpha_v = 1
        
        fig, ax = plt.subplots(figsize=(7,5))
        cmap = copy(plt.get_cmap('Blues'))
        def fmt(x, pos):
            a, b = '{:.0e}'.format(x).split('e')
            b = int(b)
            return r'${} \times 10^{{{}}}$'.format(a, b)

        if not real_n == 'ensemble':
            img = ax.imshow(kfield, cmap='jet', extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0], 
                            vmin=self.kmin, vmax=self.kmax)
        img = ax.imshow(field_resilience, cmap=cmap, extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0], 
                        vmin=0, vmax=np.ceil(field_resilience[:,:-8].max()), alpha=0.7)
        cbar = ax.figure.colorbar(img, ax=ax, fraction=0.041, pad=0.04, format=FuncFormatter(fmt))
        cbar.ax.tick_params(labelsize=14)
        cbar.ax.set_ylabel(r'$\left<R_L\right>$', fontsize=25, fontname='Arial', labelpad=10)
        cbar.solids.set_edgecolor("face")
        ax.scatter(self.observation_wells.T[0]/self.lambda_x, self.observation_wells.T[1]/self.lambda_y, 
                   color='k', marker='^' ,s=50)          
        
        ax.xaxis.set_major_locator(LinearLocator(5))
        ax.xaxis.set_minor_locator(LinearLocator(21))
        ax.yaxis.set_major_locator(LinearLocator(5))
        ax.yaxis.set_minor_locator(LinearLocator(21))
        
        rectangle2 = plt.Rectangle((self.target_xl/self.lambda_x,self.target_yl/self.lambda_y), 
                                  (self.target_xu-self.target_xl)/self.lambda_x, 
                                  (self.target_yu-self.target_yl)/self.lambda_y, 
                                  fc='k', fill=None, linewidth=1.5)
        plt.gca().add_patch(rectangle2)        
        
        plt.xlim(0,self.Lx/self.lambda_x)
        plt.ylim(0,self.Ly/self.lambda_y)
        plt.xticks(fontsize=15, fontname='Arial')
        plt.yticks(fontsize=15, fontname='Arial')
        plt.xlabel(r'$x~/~\lambda_x$', fontsize=25, fontname='Arial', labelpad=5)
        plt.ylabel(r'$y~/~\lambda_y$', fontsize=25, fontname='Arial', labelpad=5)

        plt.tight_layout()
        plt.savefig(f'figures/{filename}.png',dpi=200, bbox_inches='tight')
        
        if real_n == 'ensemble':
            fig, ax = plt.subplots(figsize=(7,5))
            cmap = copy(plt.get_cmap('Purples'))
            def fmt(x, pos):
                a, b = '{:.0e}'.format(x).split('e')
                b = int(b)
                return r'${} \times 10^{{{}}}$'.format(a, b)

            img = ax.imshow(field_resilience_var, cmap=cmap, extent=[0,self.Lx/self.lambda_x,self.Ly/self.lambda_y,0], 
                            vmin=0, vmax=np.ceil(field_resilience_var[:,:-8].max()), alpha=0.7)
            cbar = ax.figure.colorbar(img, ax=ax, fraction=0.041, pad=0.04, format=FuncFormatter(fmt))
            cbar.ax.tick_params(labelsize=14)
            cbar.ax.set_ylabel(r'$\sigma^2_{R_L}$', fontsize=25, fontname='Arial', labelpad=10)
            cbar.solids.set_edgecolor("face")
            ax.scatter(self.observation_wells.T[0]/self.lambda_x, self.observation_wells.T[1]/self.lambda_y, 
                       color='k', marker='^' ,s=50)          

            ax.xaxis.set_major_locator(LinearLocator(5))
            ax.xaxis.set_minor_locator(LinearLocator(21))
            ax.yaxis.set_major_locator(LinearLocator(5))
            ax.yaxis.set_minor_locator(LinearLocator(21))

            rectangle2 = plt.Rectangle((self.target_xl/self.lambda_x,self.target_yl/self.lambda_y), 
                                      (self.target_xu-self.target_xl)/self.lambda_x, 
                                      (self.target_yu-self.target_yl)/self.lambda_y, 
                                      fc='k', fill=None, linewidth=1.5)
            plt.gca().add_patch(rectangle2)        

            plt.xlim(0,self.Lx/self.lambda_x)
            plt.ylim(0,self.Ly/self.lambda_y)
            plt.xticks(fontsize=15, fontname='Arial')
            plt.yticks(fontsize=15, fontname='Arial')
            plt.xlabel(r'$x~/~\lambda_x$', fontsize=25, fontname='Arial', labelpad=5)
            plt.ylabel(r'$y~/~\lambda_y$', fontsize=25, fontname='Arial', labelpad=5)

            plt.tight_layout()
            plt.savefig(f'figures/{filename}.png',dpi=200, bbox_inches='tight')
            

    def eta_postprocessing(self):
        cell_number = self.Lx*self.Ly
        sflow = np.zeros((self.n_realization,self.Ly,self.Lx))

        for i in range(self.n_realization):
            velocities = []
            f = open(f'data/modflowdata/model-{i}.ftl', 'r')
            for line in f:
                if line[3] == 'X':
                    for j in range(0, cell_number, 3):
                        line = f.readline()
                        e1, e2, e3 = np.asarray(line.split(), dtype=float)
                        velocities.append(e1)
                        velocities.append(e2)
                        velocities.append(e3)
            f.close()
            sflow[i] = np.asarray(velocities).reshape((self.Ly,self.Lx))
        
        np.save('data/sflow.npy',sflow)
        
        eta = sflow[:,self.source_yl:self.source_yu,self.source_xu].mean(axis=(1))/(1/self.Lx*np.exp(np.log(self.Kg)))
        
        np.save('data/eta', eta)
        
    def maxriskresilience_postprocessing(self):
        cfield_all = np.load('data/cfields/cfield_all.npy')
        resilience_field = np.load('data/resilience_field.npy')
        maxrisk = np.zeros(self.n_realization)
        maxresilience = np.zeros(self.n_realization)
        
        for real_n in range(self.n_realization):
            field_c = cfield_all[real_n]
            field_maxrisk = np.zeros(field_c.shape)    
            field_reliability = np.zeros(field_c.shape)
            nt = len(field_c)
            c0 = field_c[0].max()
            
            field_maxrisk = np.where(field_c >= (self.mcl*c0), field_c/(self.mcl*c0), 0)
            field_resilience = resilience_field[real_n]

            maxrisk[real_n] = field_maxrisk[:,self.target_yl:self.target_yu,self.target_xl:self.target_xu].max()
            maxresilience[real_n] = field_resilience[self.target_yl:self.target_yu,self.target_xl:self.target_xu].max()
        
        np.save('data/maxrisk', maxrisk)
        np.save('data/maxresilience', maxresilience)
        
    def eta_rr(self, filename, real_n):
        eta = np.load('data/eta.npy')
        maxrisk = np.load('data/maxrisk.npy')
        maxresilience = np.load('data/maxresilience.npy')

        fig, ax = plt.subplots(figsize=(6,5))

        interp = np.linspace(0,np.ceil(eta.max()),100)
        plt.plot(interp, 293.798518*scipy.special.erf(2.375823*interp) + 449.030143, color='b', linewidth=2, label='Trend line')
        plt.scatter(eta, maxrisk, color='gray', s=25, alpha=0.8)

        if not real_n == 'ensemble':
            plt.scatter(eta[real_n], maxrisk[real_n], color='r', s=100, alpha=1, label=f'Realization {real_n}')

        ax.xaxis.set_major_locator(LinearLocator(5))
        ax.xaxis.set_minor_locator(LinearLocator(21))
        ax.yaxis.set_major_locator(LinearLocator(5))
        ax.yaxis.set_minor_locator(LinearLocator(21))

        plt.xlim(0,np.ceil(eta.max()))
        plt.ylim(0,np.ceil(maxrisk.max()*1.05))
        plt.xticks(fontsize=15, fontname='Arial')
        plt.yticks(fontsize=15, fontname='Arial')
        plt.xlabel(r'$\eta$', fontsize=25, fontname='Arial', labelpad=5)
        plt.ylabel(r'$c_{max}~/~\rm{mcl}$', fontsize=25, fontname='Arial', labelpad=5)

        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.savefig(f'figures/{filename}.png',dpi=200, bbox_inches='tight')
        plt.show()
        
        fig, ax = plt.subplots(figsize=(6,5))
        interp = np.linspace(0,np.ceil(eta.max()),100)
        plt.plot(interp, 292.155804 - 125.685574*np.log(interp), color='b', linewidth=2, label='Trend line')
        plt.scatter(eta, maxresilience, color='gray', s=25, alpha=0.8)

        if not real_n == 'ensemble':
            plt.scatter(eta[real_n], maxresilience[real_n], color='r', s=100, alpha=1, label=f'Realization {real_n}')

        ax.xaxis.set_major_locator(LinearLocator(5))
        ax.xaxis.set_minor_locator(LinearLocator(21))
        ax.yaxis.set_major_locator(LinearLocator(5))
        ax.yaxis.set_minor_locator(LinearLocator(21))

        plt.xlim(0,np.ceil(eta.max()))
        plt.ylim(0,np.ceil(maxresilience.max()*1.05))
        plt.xticks(fontsize=15, fontname='Arial')
        plt.yticks(fontsize=15, fontname='Arial')
        plt.xlabel(r'$\eta$', fontsize=25, fontname='Arial', labelpad=5)
        plt.ylabel(r'$R_L$', fontsize=25, fontname='Arial', labelpad=5)

        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.savefig(f'figures/{filename}.png',dpi=200, bbox_inches='tight')
        plt.show()
    
    def well_postprocessing(self):
        cfield_all = np.load('data/cfields/cfield_all.npy')
        obwells_conc = []
        for i in range(len(self.observation_wells)):
            obwells_conc.append(cfield_all[:,:,self.observation_wells.T[1][i],self.observation_wells.T[0][i]])
        obwells_conc = np.asarray(obwells_conc)
        obwells_maxconc = obwells_conc.max(axis=2)
        np.save('data/obwells_maxconc', obwells_maxconc)
    
    def cdf_maxconc(self, filename):
        obwells_maxconc = np.load('data/obwells_maxconc.npy' )
        
        for i in range(len(obwells_maxconc)):
            fig, ax = plt.subplots(figsize=(6,5))
            obdata = obwells_maxconc[i][obwells_maxconc[i]!=0]

            numerator = len(obwells_maxconc[i][obwells_maxconc[i]==0])
            denominator = len(obwells_maxconc[i])
            bottom_p = numerator/denominator

            hist_result, interval = np.histogram(obdata, density=True, bins=100)
            dx = interval[1] - interval[0]
            cdf_result = np.cumsum(hist_result)*dx
            cdf = (cdf_result*(1-bottom_p)) + bottom_p
            survival_p = 1 - cdf
            midpoint = (interval[:-1]+interval[1:])/2
            plt.plot(midpoint,survival_p, label=f'well {i+1}', linewidth=2,)

            param = stats.lognorm.fit(obdata)
            cdf_fitted_lognorm = stats.lognorm.cdf(midpoint, param[0], param[1], param[2])
            param = stats.beta.fit(obdata)
            cdf_fitted_beta = stats.beta.cdf(midpoint, param[0], param[1], param[2], param[3])
            survival_p_lognorm = 1 - (cdf_fitted_lognorm*(1-bottom_p) + bottom_p)
            survival_p_beta = 1 - (cdf_fitted_beta*(1-bottom_p) + bottom_p)

            plt.plot(midpoint, survival_p_lognorm,'r-', linewidth=2, label='lognorm')
            plt.plot(midpoint, survival_p_beta,'g-', linewidth=2, label='beta')            

            plt.xscale('log')
            mcl_index = np.argmin(np.abs(midpoint-self.mcl))

            print(f'the probability of the maximum concentration at the well {i+1} over {round(midpoint[mcl_index],3)} is {round(survival_p[mcl_index],3)}')

            plt.ylim(0, np.max([survival_p, survival_p_lognorm, survival_p_beta]))

            plt.xticks(fontsize=15, fontname='Arial')
            plt.yticks(fontsize=15, fontname='Arial')
            plt.xlabel(r'$c_{max}$', fontsize=25, fontname='Arial', labelpad=5)
            plt.ylabel(r'$1 - CDF$', fontsize=25, fontname='Arial', labelpad=5)
            plt.tick_params(which="major", direction="in", right=True, top=True, length=5, pad=7)
            plt.tick_params(which="minor", direction="in", right=True, top=True, length=3)
            plt.legend(fontsize=12, loc=3)
            plt.savefig(f'figures/{filename}_{i}.png',dpi=200, bbox_inches='tight')
            plt.show()
