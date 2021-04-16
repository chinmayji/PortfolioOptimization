import tkinter as tk
import pandas as pd
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from scipy.stats import norm
import math
import pdf

matplotlib.rcParams["lines.linewidth"] = 0.5


class MarGui:
    def __init__(self, name):
        self.name = name
        self.btnct = 0
        self.curr_slab = None
        self.pdf1 = pdf.PDF("pdf/transition_" + name + ".pdf")

    def launch(self):
        name = self.name

        def prm_slab(nm, default):
            mk_slab = tk.Frame(win)
            mk_slab.pack(pady=10)
            self.curr_slab = mk_slab
            mk_plt = tk.Label(mk_slab, text=nm)
            mk_plt.pack(side=tk.LEFT, padx=20)

            mk_p = tk.Entry(mk_slab)
            mk_p.insert(0, default)
            mk_p.pack(side=tk.LEFT)
            return mk_p

        def mk_btn(nm, cmd=None):
            if self.btnct % 2 == 0:
                mk_slab = tk.Frame(win)
                mk_slab.pack(pady=10)
                self.curr_slab = mk_slab

            btn = tk.Button(self.curr_slab, text=nm, command=cmd)
            btn.pack(side=tk.LEFT)
            self.btnct += 1
            return btn

        df = pd.read_csv("stkdata/" + self.name + ".csv").dropna()
        ts = df["Close Price"]

        # window config ###############################################################
        win = tk.Tk()
        screen_height = win.winfo_screenheight()
        screen_width = win.winfo_screenwidth()
        name = name
        win.title(name)
        win.minsize(int(screen_width / 5), int(screen_height / 7))

        # --------------------------

        def plf():
            plt.figure()
            plt.plot(test_data)
            plt.plot(train_data)
            plt.title(name)
            plt.xlabel("Index")
            plt.ylabel("Price")
            plt.show()

        plt_btn = tk.Button(win, text="plot", command=plf)
        plt_btn.pack()

        # --------------------------

        percent_train = prm_slab("Fraction for training", 0.9)
        extra_values = prm_slab("n(values after series)", 100)
        bracket_bound = prm_slab("bracket_boundary", 20)
        mav_days = prm_slab("n(MAV)", 50)

        # --------------------------
        ext_val = int(extra_values.get())
        per_tra = float(percent_train.get())
        n_mav = int(mav_days.get())
        data = pd.Series(ts)
        test_index = int(per_tra * len(data))
        end = len(data) + ext_val
        data_ext = pd.Series(index=range(0, end))
        for i in range(0, len(data)):
            data_ext.iloc[i] = data.iloc[i]
        per_diff_data = pd.Series(index=range(0, end))
        train_data = data[:test_index]
        test_data = data[test_index:]
        forecast_data = pd.Series(index=range(len(train_data), len(data) + ext_val))

        # create moving average series --------------------------
        def plot_mav():
            nonlocal n_mav
            n_mav = int(mav_days.get())
            tmp = data.rolling(n_mav).mean()
            i = 0
            while i < n_mav:
                mav_data.iloc[i] = data[0] + (i - 0) / n_mav * (tmp.iloc[n_mav] - data[0])
                i += 1
            while i < len(data):
                mav_data.iloc[i] = tmp.iloc[i]
                i += 1

            modl = np.poly1d(np.polyfit(range(len(data) - 100, len(data)), mav_data[len(data) - 100:len(data)], 2))
            mav_data[len(data):len(data) + ext_val] = modl(range(len(data), len(data) + ext_val))

            fig, ax = plt.subplots(ncols=2, figsize=(40, 20))

            ax[0].plot(data)
            ax[0].plot(mav_data)
            for i in range(0, len(data)):
                per_diff_data.iloc[i] = 100 * (data_ext.iloc[i] - mav_data.iloc[i]) / mav_data.iloc[i]
            ax[1].plot(per_diff_data)
            plt.show()

        mav_plot_btn = mk_btn("Plot MAV", plot_mav)
        mav_data = pd.Series(index=range(0, end))

        # get transition data ------------------
        def get_br(v):
            bb = int(bracket_bound.get())
            v = math.floor(v + 0.5)
            if v > bb:
                v = bb
            if v < -1 * bb:
                v = -1 * bb
            return int(v)

        def get_td():
            bb = int(bracket_bound.get())
            nonlocal transition_count, transition_prob, transition_cum, normal_fits
            transition_count = pd.DataFrame(np.zeros((2 * bb + 1, 2 * bb + 1)), index=range(-1 * bb, bb + 1),
                                            columns=range(-1 * bb, bb + 1),
                                            dtype=float)
            normal_fits = pd.DataFrame(index=range(-1 * bb, bb + 1),columns=[0,1])
            bb = int(bracket_bound.get())
            for i in range(1, len(train_data)):
                # print(i,per_diff_data.iat[i],data_ext.iat[i],data.iat[i])
                transition_count[get_br(per_diff_data.iat[i - 1])][get_br(per_diff_data.iat[i])] += 1
            print(transition_count)
            x = []
            y = []
            for i in range(-1 * bb, bb + 1):
                tm = []
                for j in range(-1 * bb, bb + 1):
                    for k in range(int(transition_count[i][j])):
                        x.append(i)
                        y.append(j)
                        tm.append(j)
                # plt.hist(tm,bins=range(-1 * bb, bb + 1),density=True)
                # plt.show()
                mn, sd = norm.fit(tm)
                normal_fits.loc[i] = [mn, sd]
            # print(normal_fits)
            plt.hist2d(x, y, bins=[range(-1 * bb, bb + 1), range(-1 * bb, bb + 1)])
            plt.colorbar()
            self.pdf1.add()
            plt.clf()

            transition_prob = pd.DataFrame(np.zeros((2 * bb + 1, 2 * bb + 1)), index=range(-1 * bb, bb + 1),
                                           columns=range(-1 * bb, bb + 1),
                                           dtype=float)
            for i in range(-1 * bb, bb + 1):
                sm = 0
                for j in range(-1 * bb, bb + 1):
                    sm += transition_count[i][j]
                for j in range(-1 * bb, bb + 1):
                    transition_prob[i][j] = transition_count[i][j] / sm
            # transition_prob.to_csv("t1.csv")
            transition_cum = pd.DataFrame(np.zeros((2 * bb + 1, 2 * bb + 1)), index=range(-1 * bb, bb + 1),
                                          columns=range(-1 * bb, bb + 1),
                                          dtype=float)
            for i in range(-1 * bb, bb + 1):
                sm = 0
                for j in range(-1 * bb, bb + 1):
                    transition_cum[i][j] = transition_prob[i][j] + sm
                    sm = transition_cum[i][j]
            transition_cum.to_csv("tmp.csv")

            for i in range(-1 * bb, bb + 1):
                plt.bar(range(-1 * bb, bb + 1), transition_prob[i])
                plt.title("Transition frequency from " + str(i) + " to x axis values")
                plt.xticks(range(-1 * bb, bb + 1), range(-1 * bb, bb + 1), rotation='vertical')
                plt.plot(range(-1 * bb, bb + 1), norm.pdf(range(-1 * bb, bb + 1), normal_fits.loc[i,0], normal_fits.loc[i,1]),color='red')
                self.pdf1.add()
                plt.clf()
            self.pdf1.save()
            print("save")

            for i in range(-1 * bb, bb + 1):
                mn, sd = norm.fit(transition_prob)

        transition_data_btn = mk_btn("Get Transition Data", get_td)
        transition_count = None
        transition_prob = None
        transition_cum = None
        normal_fits = None

        # forecast ----------------------------------
        pred_per_diff = pd.Series(index=range(len(train_data) - 1, end))

        def forecast():
            pred_per_diff.loc[len(train_data) - 1] = per_diff_data.iloc[len(train_data) - 1]
            bb = int(bracket_bound.get())
            for i in range(len(train_data), len(data) + ext_val):
                rd = np.random.random()
                br = get_br(pred_per_diff.loc[i - 1])
                j = -1 * bb
                # print(rd, br)
                while rd >= transition_cum[br][j]:
                    j += 1
                pred_per_diff.loc[i] = j

            for i in range(len(train_data), len(data) + ext_val):
                mv = mav_data.iloc[i]
                forecast_data.loc[i] = mv + pred_per_diff.loc[i] * mv / 100
                # print(i,mv,forecast_data.loc[i])
            plt.close()
            fig, ax = plt.subplots(ncols=2, figsize=(40, 20))
            ax[0].plot(pred_per_diff)
            ax[1].plot(mav_data)
            ax[1].plot(train_data)
            ax[1].plot(test_data)
            ax[1].plot(forecast_data)
            ax[1].legend(["Moving Average", "Train Data", "Test Data", "Forecast Data"])
            plt.show()

        forecast_btn = mk_btn("forecast", forecast)

        # forecast2 ---------------------------------

        def forecast2():
            pred_per_diff.loc[len(train_data) - 1] = per_diff_data.iloc[len(train_data) - 1]
            bb = int(bracket_bound.get())
            for i in range(len(train_data), len(data) + ext_val):
                br = get_br(pred_per_diff.loc[i - 1])
                j = -1 * bb
                pred_per_diff.loc[i] = np.random.normal(normal_fits.loc[br,0],normal_fits.loc[br,1])

            for i in range(len(train_data), len(data) + ext_val):
                mv = mav_data.iloc[i]
                forecast_data.loc[i] = mv + pred_per_diff.loc[i] * mv / 100
                # print(i,mv,forecast_data.loc[i])
            plt.close()
            fig, ax = plt.subplots(ncols=2, figsize=(40, 20))
            ax[0].plot(pred_per_diff)
            ax[1].plot(mav_data)
            ax[1].plot(train_data)
            ax[1].plot(test_data)
            ax[1].plot(forecast_data)
            ax[1].legend(["Moving Average", "Train Data", "Test Data", "Forecast Data"])
            plt.show()

        forecast2_btn = mk_btn("forecast_normal", forecast2)

        # make plot pdf -----------------------------

        # ---------------------------
        win.mainloop()