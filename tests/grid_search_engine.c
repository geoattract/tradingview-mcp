#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <pthread.h>
#include <stdbool.h>

#define MAX_BARS 20000
#define NUM_THREADS 8
#define OCT_1_TS 1790812800LL
#define FRICTION_PTS 1.20
#define POINT_VAL 2.0

typedef struct {
    long long time;
    double open;
    double high;
    double low;
    double close;
    double volume;
} Bar;

static Bar bars[MAX_BARS];
static int N = 0;
static int oct1_idx = 0;

// Parameter Grid Definitions
static const int atr_periods[] = {10, 14, 20, 50, 80, 100};
#define NUM_PERIODS 6

static const double multipliers[] = {1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0};
#define NUM_MULTS 7

static const char* methods[] = {"SMA", "RMA", "EMA"};
#define NUM_METHODS 3

static const char* sources[] = {"hl2", "close"};
#define NUM_SOURCES 2

#define NUM_ST_CONFIGS (NUM_PERIODS * NUM_MULTS * NUM_METHODS * NUM_SOURCES) // 252

// Stoch RSI Pullback parameters
// zone_mode: 0: <=30/>=70, 1: <=20/>=80, 2: Anywhere
static const char* zone_modes[] = {
    "Cross in Zone (<=30 / >=70)",
    "Cross in Zone (<=20 / >=80)",
    "Cross Anywhere in Trend"
};
#define NUM_ZONES 3

static const int rsi_lengths[] = {10, 14};
#define NUM_RSI_LENS 2

static const int req_candles[] = {0, 1}; // False, True
#define NUM_CANDLES 2

static const int cooldowns[] = {2, 3, 5};
#define NUM_COOLDOWNS 3

#define NUM_PB_CONFIGS (NUM_ZONES * NUM_RSI_LENS * NUM_CANDLES * NUM_COOLDOWNS) // 36

// Early Turning Dot OS/OB levels
typedef struct {
    double os;
    double ob;
} DotLevel;

static const DotLevel dot_levels[] = {
    {25.0, 60.0}, {25.0, 65.0}, {25.0, 70.0},
    {30.0, 60.0}, {30.0, 65.0}, {30.0, 70.0},
    {35.0, 60.0}, {35.0, 65.0}, {35.0, 70.0}
};
#define NUM_DOT_CONFIGS 9

#define TOTAL_COMBINATIONS (NUM_ST_CONFIGS * NUM_PB_CONFIGS * NUM_DOT_CONFIGS) // 81,648

// Precalculated arrays
// 1. Supertrend series: 252 configs
static int8_t st_trend[NUM_ST_CONFIGS][MAX_BARS];

// 2. Early Turning Dots: 2 sources x 9 dot_levels = 18 configs
static uint8_t g_dots[2][NUM_DOT_CONFIGS][MAX_BARS];
static uint8_t y_dots[2][NUM_DOT_CONFIGS][MAX_BARS];

// 3. Stoch RSI Raw Conditions: 2 rsi_lens x 3 zones x 2 candles = 12 configs
static uint8_t pb_cond_buy[NUM_RSI_LENS][NUM_ZONES][NUM_CANDLES][MAX_BARS];
static uint8_t pb_cond_sell[NUM_RSI_LENS][NUM_ZONES][NUM_CANDLES][MAX_BARS];

// Result structure
typedef struct {
    int st_idx;
    int p_period;
    double p_mult;
    int p_method; // 0=SMA, 1=RMA, 2=EMA
    int p_source; // 0=hl2, 1=close
    
    int p_zone_mode;
    int p_rsi_len;
    int p_req_candle;
    int p_cooldown;
    
    double p_dot_os;
    double p_dot_ob;
    
    int trades;
    int wins;
    int losses;
    double win_rate;
    double net_pts;
    double net_usd;
    double gross_win_pts;
    double gross_loss_pts;
    double profit_factor;
    double max_dd_pts;
    double max_dd_usd;
    double avg_trade_pts;
    double avg_trade_usd;
    
    // Pure ST baseline metrics
    double pure_st_net_pts;
    double pure_st_pf;
    double pure_st_max_dd_pts;
    int pure_st_trades;
} SimResult;

static SimResult results[TOTAL_COMBINATIONS];

// Load CSV
int load_data(const char* filepath) {
    FILE* f = fopen(filepath, "r");
    if (!f) return -1;
    char line[256];
    if (!fgets(line, sizeof(line), f)) { fclose(f); return -1; }
    N = 0;
    while (fgets(line, sizeof(line), f)) {
        if (N >= MAX_BARS) break;
        sscanf(line, "%lld,%lf,%lf,%lf,%lf,%lf",
               &bars[N].time, &bars[N].open, &bars[N].high,
               &bars[N].low, &bars[N].close, &bars[N].volume);
        if (oct1_idx == 0 && bars[N].time >= OCT_1_TS) {
            oct1_idx = N;
        }
        N++;
    }
    fclose(f);
    return N;
}

// Technical indicator helpers
static double tr[MAX_BARS];
static double rsi_hl2_14[MAX_BARS];
static double rsi_close_14[MAX_BARS];
static double rsi_close_10[MAX_BARS];
static double rsi_ma_hl2_14[MAX_BARS];
static double rsi_ma_close_14[MAX_BARS];

void calc_rsi_series(const double* src, int len, double* out) {
    double up_chg[MAX_BARS] = {0};
    double dn_chg[MAX_BARS] = {0};
    for (int i = 1; i < N; i++) {
        double d = src[i] - src[i-1];
        if (d > 0) up_chg[i] = d;
        else dn_chg[i] = -d;
    }
    double avg_up[MAX_BARS] = {0};
    double avg_dn[MAX_BARS] = {0};
    double alpha = 1.0 / len;
    double s_up = 0, s_dn = 0;
    for (int i = 0; i < N; i++) {
        if (i < len) {
            s_up += up_chg[i];
            s_dn += dn_chg[i];
            avg_up[i] = s_up / (i + 1);
            avg_dn[i] = s_dn / (i + 1);
        } else {
            avg_up[i] = alpha * up_chg[i] + (1.0 - alpha) * avg_up[i-1];
            avg_dn[i] = alpha * dn_chg[i] + (1.0 - alpha) * avg_dn[i-1];
        }
        if (avg_dn[i] == 0) out[i] = 100.0;
        else if (avg_up[i] == 0) out[i] = 0.0;
        else out[i] = 100.0 - (100.0 / (1.0 + avg_up[i] / avg_dn[i]));
    }
}

void calc_wma_14(const double* src, double* out) {
    int len = 14;
    double w_sum = 14 * 15 / 2.0; // 105.0
    for (int i = 0; i < N; i++) {
        if (i < len - 1) {
            double s = 0, cur_w_sum = 0;
            for (int k = 0; k <= i; k++) {
                double w = k + 1;
                s += src[k] * w;
                cur_w_sum += w;
            }
            out[i] = s / cur_w_sum;
        } else {
            double s = 0;
            for (int k = 0; k < len; k++) {
                s += src[i - len + 1 + k] * (k + 1);
            }
            out[i] = s / w_sum;
        }
    }
}

void compute_technical_bases() {
    tr[0] = bars[0].high - bars[0].low;
    for (int i = 1; i < N; i++) {
        double hl = bars[i].high - bars[i].low;
        double hc = fabs(bars[i].high - bars[i-1].close);
        double lc = fabs(bars[i].low - bars[i-1].close);
        double m = hl > hc ? hl : hc;
        tr[i] = m > lc ? m : lc;
    }
    
    double hl2[MAX_BARS];
    double cl[MAX_BARS];
    for (int i = 0; i < N; i++) {
        hl2[i] = (bars[i].high + bars[i].low) / 2.0;
        cl[i] = bars[i].close;
    }
    
    calc_rsi_series(hl2, 14, rsi_hl2_14);
    calc_rsi_series(cl, 14, rsi_close_14);
    calc_rsi_series(cl, 10, rsi_close_10);
    
    calc_wma_14(rsi_hl2_14, rsi_ma_hl2_14);
    calc_wma_14(rsi_close_14, rsi_ma_close_14);
}

// 1. Precalculate all 252 Supertrend series
void precalculate_supertrends() {
    int cfg_idx = 0;
    for (int p_idx = 0; p_idx < NUM_PERIODS; p_idx++) {
        int period = atr_periods[p_idx];
        
        // Calculate ATR for 3 methods
        double atr_sma[MAX_BARS];
        double atr_rma[MAX_BARS];
        double atr_ema[MAX_BARS];
        
        // SMA
        double s = 0;
        for (int i = 0; i < N; i++) {
            s += tr[i];
            if (i >= period) {
                s -= tr[i - period];
                atr_sma[i] = s / period;
            } else {
                atr_sma[i] = s / (i + 1);
            }
        }
        
        // RMA (Wilder)
        double rma_alpha = 1.0 / period;
        double rma_s = 0;
        for (int i = 0; i < N; i++) {
            if (i < period) {
                rma_s += tr[i];
                atr_rma[i] = rma_s / (i + 1);
            } else {
                atr_rma[i] = rma_alpha * tr[i] + (1.0 - rma_alpha) * atr_rma[i-1];
            }
        }
        
        // EMA
        double ema_alpha = 2.0 / (period + 1.0);
        double ema_s = 0;
        for (int i = 0; i < N; i++) {
            if (i < period) {
                ema_s += tr[i];
                atr_ema[i] = ema_s / (i + 1);
            } else {
                atr_ema[i] = ema_alpha * tr[i] + (1.0 - ema_alpha) * atr_ema[i-1];
            }
        }
        
        for (int m_idx = 0; m_idx < NUM_MULTS; m_idx++) {
            double mult = multipliers[m_idx];
            
            for (int met_idx = 0; met_idx < NUM_METHODS; met_idx++) {
                double* atr_cur = (met_idx == 0) ? atr_sma : (met_idx == 1 ? atr_rma : atr_ema);
                
                for (int src_idx = 0; src_idx < NUM_SOURCES; src_idx++) {
                    double up[MAX_BARS];
                    double dn[MAX_BARS];
                    int8_t* trend = st_trend[cfg_idx];
                    
                    for (int i = 0; i < N; i++) {
                        double src = (src_idx == 0) ? ((bars[i].high + bars[i].low) / 2.0) : bars[i].close;
                        double b_up = src - mult * atr_cur[i];
                        double b_dn = src + mult * atr_cur[i];
                        
                        if (i == 0) {
                            up[0] = b_up;
                            dn[0] = b_dn;
                            trend[0] = 1;
                        } else {
                            up[i] = (bars[i-1].close > up[i-1]) ? (b_up > up[i-1] ? b_up : up[i-1]) : b_up;
                            dn[i] = (bars[i-1].close < dn[i-1]) ? (b_dn < dn[i-1] ? b_dn : dn[i-1]) : b_dn;
                            
                            if (trend[i-1] == -1 && bars[i].close > dn[i-1]) {
                                trend[i] = 1;
                            } else if (trend[i-1] == 1 && bars[i].close < up[i-1]) {
                                trend[i] = -1;
                            } else {
                                trend[i] = trend[i-1];
                            }
                        }
                    }
                    cfg_idx++;
                }
            }
        }
    }
}

// 2. Precalculate Early Turning Dots (18 configs)
void precalculate_turning_dots() {
    for (int src_idx = 0; src_idx < NUM_SOURCES; src_idx++) {
        double* rsiVal = (src_idx == 0) ? rsi_hl2_14 : rsi_close_14;
        double* rsiMa = (src_idx == 0) ? rsi_ma_hl2_14 : rsi_ma_close_14;
        double* rsiCloseVal = rsi_close_14;
        
        for (int d_idx = 0; d_idx < NUM_DOT_CONFIGS; d_idx++) {
            double dotOsLevel = dot_levels[d_idx].os;
            double dotObLevel = dot_levels[d_idx].ob;
            
            uint8_t* g_dot = g_dots[src_idx][d_idx];
            uint8_t* y_dot = y_dots[src_idx][d_idx];
            memset(g_dot, 0, N);
            memset(y_dot, 0, N);
            
            bool armBullDot = false;
            bool armBearDot = false;
            int lastBullTouchBar = -9999;
            int lastBearTouchBar = -9999;
            int dotTrend = 0;
            int lastAnyDotBar = -9999;
            
            for (int i = 1; i < N; i++) {
                double minSensor = rsiVal[i] < rsiCloseVal[i] ? rsiVal[i] : rsiCloseVal[i];
                double maxSensor = rsiVal[i] > rsiCloseVal[i] ? rsiVal[i] : rsiCloseVal[i];
                
                bool canArmBull = (dotTrend != 1);
                bool canArmBear = (dotTrend != -1);
                
                if (minSensor <= dotOsLevel && canArmBull) {
                    armBullDot = true;
                    lastBullTouchBar = i;
                }
                if (maxSensor >= dotObLevel && canArmBear) {
                    armBearDot = true;
                    lastBearTouchBar = i;
                }
                
                bool bullWithinMemory = armBullDot && ((i - lastBullTouchBar) <= 8);
                bool bearWithinMemory = armBearDot && ((i - lastBearTouchBar) <= 8);
                
                bool rsiCrossUp = (rsiVal[i] > rsiMa[i] && rsiVal[i-1] <= rsiMa[i-1]);
                bool rsiCrossDn = (rsiVal[i] < rsiMa[i] && rsiVal[i-1] >= rsiMa[i-1]);
                bool bullTurn = (rsiVal[i] > rsiVal[i-1]) || rsiCrossUp;
                bool bearTurn = (rsiVal[i] < rsiVal[i-1]) || rsiCrossDn;
                
                double candleRng = (bars[i].high - bars[i].low) > 1e-5 ? (bars[i].high - bars[i].low) : 1e-5;
                bool isGreenCandle = bars[i].close > bars[i].open;
                bool isRedCandle = bars[i].close < bars[i].open;
                
                bool bullHighBreak = bars[i].close > bars[i-1].high;
                bool bullEngulfing = (bars[i].close > bars[i-1].open) && (bars[i].open <= bars[i-1].close);
                bool bullPinReject = (bars[i].close - bars[i].low) >= 0.65 * candleRng;
                bool bullStructureOk = isGreenCandle && (bullHighBreak || bullEngulfing || bullPinReject);
                
                bool bearLowBreak = bars[i].close < bars[i-1].low;
                bool bearEngulfing = (bars[i].close < bars[i-1].open) && (bars[i].open >= bars[i-1].close);
                bool bearPinReject = (bars[i].high - bars[i].close) >= 0.65 * candleRng;
                bool bearStructureOk = isRedCandle && (bearLowBreak || bearEngulfing || bearPinReject);
                
                bool spacingOk = (i - lastAnyDotBar) >= 4;
                
                if (bullWithinMemory && bullTurn && bullStructureOk && (dotTrend != 1) && spacingOk) {
                    dotTrend = 1;
                    lastAnyDotBar = i;
                    armBullDot = false;
                    armBearDot = false;
                    g_dot[i] = 1;
                } else if (bearWithinMemory && bearTurn && bearStructureOk && (dotTrend != -1) && spacingOk) {
                    dotTrend = -1;
                    lastAnyDotBar = i;
                    armBearDot = false;
                    armBullDot = false;
                    y_dot[i] = 1;
                }
                
                if (armBullDot && (((i - lastBullTouchBar) > 8) || (rsiVal[i] > 50.0))) armBullDot = false;
                if (armBearDot && (((i - lastBearTouchBar) > 8) || (rsiVal[i] < 50.0))) armBearDot = false;
            }
        }
    }
}

// 3. Precalculate Stoch RSI raw conditions (12 configs)
void precalculate_pullback_conditions() {
    for (int r_idx = 0; r_idx < NUM_RSI_LENS; r_idx++) {
        double* rsi = (r_idx == 0) ? rsi_close_10 : rsi_close_14;
        
        double stoch[MAX_BARS];
        int stoch_len = 14;
        for (int i = 0; i < N; i++) {
            double lo = 1e9, hi = -1e9;
            int start_k = (i - stoch_len + 1) >= 0 ? (i - stoch_len + 1) : 0;
            for (int k = start_k; k <= i; k++) {
                if (rsi[k] < lo) lo = rsi[k];
                if (rsi[k] > hi) hi = rsi[k];
            }
            stoch[i] = (hi > lo) ? ((rsi[i] - lo) / (hi - lo) * 100.0) : 50.0;
        }
        
        // SMA 3 of stoch = %K
        double stochK[MAX_BARS];
        double s_k = 0;
        for (int i = 0; i < N; i++) {
            s_k += stoch[i];
            if (i >= 3) { s_k -= stoch[i-3]; stochK[i] = s_k / 3.0; }
            else stochK[i] = s_k / (i + 1);
        }
        
        // SMA 3 of %K = %D
        double stochD[MAX_BARS];
        double s_d = 0;
        for (int i = 0; i < N; i++) {
            s_d += stochK[i];
            if (i >= 3) { s_d -= stochK[i-3]; stochD[i] = s_d / 3.0; }
            else stochD[i] = s_d / (i + 1);
        }
        
        // Lowest & Highest over 3 bars
        double lowestK[MAX_BARS], lowestD[MAX_BARS], lowestS[MAX_BARS];
        double highestK[MAX_BARS], highestD[MAX_BARS], highestS[MAX_BARS];
        for (int i = 0; i < N; i++) {
            int start_w = (i - 2 >= 0) ? (i - 2) : 0;
            double l_k = 1e9, l_d = 1e9, l_s = 1e9;
            double h_k = -1e9, h_d = -1e9, h_s = -1e9;
            for (int k = start_w; k <= i; k++) {
                if (stochK[k] < l_k) l_k = stochK[k];
                if (stochD[k] < l_d) l_d = stochD[k];
                if (stoch[k] < l_s) l_s = stoch[k];
                if (stochK[k] > h_k) h_k = stochK[k];
                if (stochD[k] > h_d) h_d = stochD[k];
                if (stoch[k] > h_s) h_s = stoch[k];
            }
            lowestK[i] = l_k; lowestD[i] = l_d; lowestS[i] = l_s;
            highestK[i] = h_k; highestD[i] = h_d; highestS[i] = h_s;
        }
        
        for (int z_idx = 0; z_idx < NUM_ZONES; z_idx++) {
            double os_thresh = (z_idx == 0) ? 30.0 : (z_idx == 1 ? 20.0 : 999.0);
            double ob_thresh = (z_idx == 0) ? 70.0 : (z_idx == 1 ? 80.0 : -999.0);
            
            for (int c_idx = 0; c_idx < NUM_CANDLES; c_idx++) {
                int req_candle = req_candles[c_idx];
                
                uint8_t* buy_cond = pb_cond_buy[r_idx][z_idx][c_idx];
                uint8_t* sell_cond = pb_cond_sell[r_idx][z_idx][c_idx];
                memset(buy_cond, 0, N);
                memset(sell_cond, 0, N);
                
                for (int i = 1; i < N; i++) {
                    bool kCrossOver = (stochK[i] > stochD[i] && stochK[i-1] <= stochD[i-1]);
                    bool kCrossUnder = (stochK[i] < stochD[i] && stochK[i-1] >= stochD[i-1]);
                    
                    bool inZoneBuy = (z_idx == 2) || (lowestK[i] <= os_thresh || lowestD[i] <= os_thresh || lowestS[i] <= os_thresh);
                    bool inZoneSell = (z_idx == 2) || (highestK[i] >= ob_thresh || highestD[i] >= ob_thresh || highestS[i] >= ob_thresh);
                    
                    bool candleOkBuy = (!req_candle) || (bars[i].close > bars[i].open);
                    bool candleOkSell = (!req_candle) || (bars[i].close < bars[i].open);
                    
                    if (kCrossOver && inZoneBuy && candleOkBuy) buy_cond[i] = 1;
                    if (kCrossUnder && inZoneSell && candleOkSell) sell_cond[i] = 1;
                }
            }
        }
    }
}

// Thread worker
typedef struct {
    int thread_id;
    int start_combo;
    int end_combo;
} ThreadArg;

void* simulate_combos(void* arg) {
    ThreadArg* targ = (ThreadArg*)arg;
    
    // Arrays for trade tracking inside a simulation run
    #define MAX_TRADES 3000
    double trade_pnls[MAX_TRADES];
    
    for (int combo = targ->start_combo; combo < targ->end_combo; combo++) {
        // Decode combo indices
        int rem = combo;
        
        int d_idx = rem % NUM_DOT_CONFIGS; rem /= NUM_DOT_CONFIGS;
        int cd_idx = rem % NUM_COOLDOWNS; rem /= NUM_COOLDOWNS;
        int c_idx = rem % NUM_CANDLES; rem /= NUM_CANDLES;
        int r_idx = rem % NUM_RSI_LENS; rem /= NUM_RSI_LENS;
        int z_idx = rem % NUM_ZONES; rem /= NUM_ZONES;
        int src_idx = rem % NUM_SOURCES; rem /= NUM_SOURCES;
        int met_idx = rem % NUM_METHODS; rem /= NUM_METHODS;
        int m_idx = rem % NUM_MULTS; rem /= NUM_MULTS;
        int p_idx = rem % NUM_PERIODS;
        
        int st_idx = p_idx * (NUM_MULTS * NUM_METHODS * NUM_SOURCES) +
                     m_idx * (NUM_METHODS * NUM_SOURCES) +
                     met_idx * NUM_SOURCES +
                     src_idx;
                     
        int cooldown = cooldowns[cd_idx];
        
        const int8_t* trend = st_trend[st_idx];
        const uint8_t* g_dot = g_dots[src_idx][d_idx];
        const uint8_t* y_dot = y_dots[src_idx][d_idx];
        const uint8_t* buy_cond = pb_cond_buy[r_idx][z_idx][c_idx];
        const uint8_t* sell_cond = pb_cond_sell[r_idx][z_idx][c_idx];
        
        int n_trades = 0;
        int pos = 0; // 1 = Long, -1 = Short, 0 = Flat
        double entry_price = 0.0;
        int last_pb = -9999;
        
        // Warmup before oct1_idx
        for (int i = 1; i < oct1_idx; i++) {
            if (trend[i] != trend[i-1]) {
                pos = trend[i];
                entry_price = bars[i+1].open;
            } else if (pos == 1 && y_dot[i] && trend[i] == 1) {
                pos = 0;
            } else if (pos == -1 && g_dot[i] && trend[i] == -1) {
                pos = 0;
            } else if (pos == 0) {
                if (trend[i] == 1 && trend[i-1] == 1 && buy_cond[i] && (i - last_pb >= cooldown)) {
                    pos = 1;
                    entry_price = bars[i+1].open;
                    last_pb = i;
                } else if (trend[i] == -1 && trend[i-1] == -1 && sell_cond[i] && (i - last_pb >= cooldown)) {
                    pos = -1;
                    entry_price = bars[i+1].open;
                    last_pb = i;
                }
            } else {
                if (trend[i] == 1 && trend[i-1] == 1 && buy_cond[i] && (i - last_pb >= cooldown)) last_pb = i;
                else if (trend[i] == -1 && trend[i-1] == -1 && sell_cond[i] && (i - last_pb >= cooldown)) last_pb = i;
            }
        }
        
        // Active evaluation window
        for (int i = oct1_idx; i < N - 1; i++) {
            double exec_price = bars[i+1].open;
            
            // 1. Supertrend Flip
            if (trend[i] != trend[i-1]) {
                if (pos != 0 && n_trades < MAX_TRADES) {
                    double pnl = (pos == 1) ? (exec_price - entry_price) : (entry_price - exec_price);
                    trade_pnls[n_trades++] = pnl - FRICTION_PTS;
                }
                pos = trend[i];
                entry_price = exec_price;
                continue;
            }
            
            // 2. Early TP
            if (pos == 1 && y_dot[i] && trend[i] == 1) {
                if (n_trades < MAX_TRADES) {
                    double pnl = exec_price - entry_price;
                    trade_pnls[n_trades++] = pnl - FRICTION_PTS;
                }
                pos = 0;
                continue;
            } else if (pos == -1 && g_dot[i] && trend[i] == -1) {
                if (n_trades < MAX_TRADES) {
                    double pnl = entry_price - exec_price;
                    trade_pnls[n_trades++] = pnl - FRICTION_PTS;
                }
                pos = 0;
                continue;
            }
            
            // 3. Pullback Re-entry
            if (pos == 0) {
                if (trend[i] == 1 && trend[i-1] == 1 && buy_cond[i] && (i - last_pb >= cooldown)) {
                    pos = 1;
                    entry_price = exec_price;
                    last_pb = i;
                } else if (trend[i] == -1 && trend[i-1] == -1 && sell_cond[i] && (i - last_pb >= cooldown)) {
                    pos = -1;
                    entry_price = exec_price;
                    last_pb = i;
                }
            } else {
                if (trend[i] == 1 && trend[i-1] == 1 && buy_cond[i] && (i - last_pb >= cooldown)) last_pb = i;
                else if (trend[i] == -1 && trend[i-1] == -1 && sell_cond[i] && (i - last_pb >= cooldown)) last_pb = i;
            }
        }
        
        // Final bar mark-to-market
        if (pos != 0 && n_trades < MAX_TRADES) {
            double exec_price = bars[N-1].close;
            double pnl = (pos == 1) ? (exec_price - entry_price) : (entry_price - exec_price);
            trade_pnls[n_trades++] = pnl - FRICTION_PTS;
        }
        
        // Compute statistics
        int wins = 0, losses = 0;
        double net_pts = 0.0;
        double gross_win = 0.0;
        double gross_loss = 0.0;
        double cum = 0.0, peak = 0.0, max_dd = 0.0;
        
        for (int t = 0; t < n_trades; t++) {
            double p = trade_pnls[t];
            net_pts += p;
            if (p > 0) {
                wins++;
                gross_win += p;
            } else {
                losses++;
                gross_loss += fabs(p);
            }
            cum += p;
            if (cum > peak) peak = cum;
            double dd = peak - cum;
            if (dd > max_dd) max_dd = dd;
        }
        
        SimResult* r = &results[combo];
        r->st_idx = st_idx;
        r->p_period = atr_periods[p_idx];
        r->p_mult = multipliers[m_idx];
        r->p_method = met_idx;
        r->p_source = src_idx;
        r->p_zone_mode = z_idx;
        r->p_rsi_len = rsi_lengths[r_idx];
        r->p_req_candle = req_candles[c_idx];
        r->p_cooldown = cooldown;
        r->p_dot_os = dot_levels[d_idx].os;
        r->p_dot_ob = dot_levels[d_idx].ob;
        
        r->trades = n_trades;
        r->wins = wins;
        r->losses = losses;
        r->win_rate = n_trades > 0 ? ((double)wins / n_trades * 100.0) : 0.0;
        r->net_pts = net_pts;
        r->net_usd = net_pts * POINT_VAL;
        r->gross_win_pts = gross_win;
        r->gross_loss_pts = gross_loss;
        r->profit_factor = gross_loss > 0 ? (gross_win / gross_loss) : 999.0;
        r->max_dd_pts = max_dd;
        r->max_dd_usd = max_dd * POINT_VAL;
        r->avg_trade_pts = n_trades > 0 ? (net_pts / n_trades) : 0.0;
        r->avg_trade_usd = r->avg_trade_pts * POINT_VAL;
    }
    
    return NULL;
}

// Compute pure Supertrend baselines for all 252 ST configs
static double pure_st_net[NUM_ST_CONFIGS];
static double pure_st_pf_arr[NUM_ST_CONFIGS];
static double pure_st_dd_arr[NUM_ST_CONFIGS];
static int pure_st_tr_arr[NUM_ST_CONFIGS];

void compute_pure_st_baselines() {
    double trade_pnls[MAX_TRADES];
    
    for (int st_idx = 0; st_idx < NUM_ST_CONFIGS; st_idx++) {
        const int8_t* trend = st_trend[st_idx];
        int n_trades = 0;
        int pos = 0;
        double entry_price = 0.0;
        
        for (int i = 1; i < oct1_idx; i++) {
            if (trend[i] != trend[i-1]) {
                pos = trend[i];
                entry_price = bars[i+1].open;
            }
        }
        
        for (int i = oct1_idx; i < N - 1; i++) {
            if (trend[i] != trend[i-1]) {
                double exec_price = bars[i+1].open;
                if (pos != 0 && n_trades < MAX_TRADES) {
                    double pnl = (pos == 1) ? (exec_price - entry_price) : (entry_price - exec_price);
                    trade_pnls[n_trades++] = pnl - FRICTION_PTS;
                }
                pos = trend[i];
                entry_price = exec_price;
            }
        }
        
        if (pos != 0 && n_trades < MAX_TRADES) {
            double exec_price = bars[N-1].close;
            double pnl = (pos == 1) ? (exec_price - entry_price) : (entry_price - exec_price);
            trade_pnls[n_trades++] = pnl - FRICTION_PTS;
        }
        
        double net = 0, gw = 0, gl = 0, cum = 0, peak = 0, dd = 0;
        for (int t = 0; t < n_trades; t++) {
            double p = trade_pnls[t];
            net += p;
            if (p > 0) gw += p; else gl += fabs(p);
            cum += p;
            if (cum > peak) peak = cum;
            if (peak - cum > dd) dd = peak - cum;
        }
        
        pure_st_net[st_idx] = net;
        pure_st_pf_arr[st_idx] = gl > 0 ? (gw / gl) : 999.0;
        pure_st_dd_arr[st_idx] = dd;
        pure_st_tr_arr[st_idx] = n_trades;
    }
}

int main() {
    printf("=================================================================\\n");
    printf("Supertrend V4 + RSI Full Grid Search Optimization Engine\\n");
    printf("=================================================================\\n");
    
    if (load_data("mnq_5m_data.csv") <= 0) {
        fprintf(stderr, "Failed to load mnq_5m_data.csv\\n");
        return 1;
    }
    printf("Loaded %d bars. Oct 1 evaluation starts at bar %d.\\n", N, oct1_idx);
    
    compute_technical_bases();
    printf("Computed technical base indicators.\\n");
    
    precalculate_supertrends();
    printf("Precalculated %d Supertrend series.\\n", NUM_ST_CONFIGS);
    
    precalculate_turning_dots();
    printf("Precalculated 18 Early Turning Dot series.\\n");
    
    precalculate_pullback_conditions();
    printf("Precalculated 12 Stoch RSI Pullback condition series.\\n");
    
    compute_pure_st_baselines();
    printf("Computed pure Supertrend baselines.\\n");
    
    // Launch threads
    pthread_t threads[NUM_THREADS];
    ThreadArg targs[NUM_THREADS];
    int per_thread = TOTAL_COMBINATIONS / NUM_THREADS;
    
    for (int t = 0; t < NUM_THREADS; t++) {
        targs[t].thread_id = t;
        targs[t].start_combo = t * per_thread;
        targs[t].end_combo = (t == NUM_THREADS - 1) ? TOTAL_COMBINATIONS : (t + 1) * per_thread;
        pthread_create(&threads[t], NULL, simulate_combos, &targs[t]);
    }
    
    for (int t = 0; t < NUM_THREADS; t++) {
        pthread_join(threads[t], NULL);
    }
    printf("Simulated all %d combinations successfully.\\n", TOTAL_COMBINATIONS);
    
    // Attach pure ST baselines
    for (int i = 0; i < TOTAL_COMBINATIONS; i++) {
        int st_id = results[i].st_idx;
        results[i].pure_st_net_pts = pure_st_net[st_id];
        results[i].pure_st_pf = pure_st_pf_arr[st_id];
        results[i].pure_st_max_dd_pts = pure_st_dd_arr[st_id];
        results[i].pure_st_trades = pure_st_tr_arr[st_id];
    }
    
    // Save results to binary file for instant python analysis
    FILE* f_bin = fopen("grid_search_results.bin", "wb");
    if (f_bin) {
        fwrite(results, sizeof(SimResult), TOTAL_COMBINATIONS, f_bin);
        fclose(f_bin);
        printf("Saved grid_search_results.bin (%lu bytes).\\n", sizeof(SimResult) * TOTAL_COMBINATIONS);
    }
    
    // Save CSV
    FILE* f_csv = fopen("grid_search_results.csv", "w");
    if (f_csv) {
        fprintf(f_csv, "st_idx,period,mult,method,source,zone_mode,rsi_len,req_candle,cooldown,dot_os,dot_ob,"
                       "trades,wins,losses,win_rate,net_pts,net_usd,pf,max_dd_pts,max_dd_usd,avg_pts,avg_usd,"
                       "pure_st_net_pts,pure_st_pf,pure_st_max_dd_pts,pure_st_trades\n");
        for (int i = 0; i < TOTAL_COMBINATIONS; i++) {
            SimResult* r = &results[i];
            fprintf(f_csv, "%d,%d,%.1f,%s,%s,%s,%d,%d,%d,%.1f,%.1f,%d,%d,%d,%.2f,%.2f,%.2f,%.3f,%.2f,%.2f,%.2f,%.2f,%.2f,%.3f,%.2f,%d\n",
                    r->st_idx, r->p_period, r->p_mult, methods[r->p_method], sources[r->p_source],
                    zone_modes[r->p_zone_mode], r->p_rsi_len, r->p_req_candle, r->p_cooldown,
                    r->p_dot_os, r->p_dot_ob,
                    r->trades, r->wins, r->losses, r->win_rate, r->net_pts, r->net_usd, r->profit_factor,
                    r->max_dd_pts, r->max_dd_usd, r->avg_trade_pts, r->avg_trade_usd,
                    r->pure_st_net_pts, r->pure_st_pf, r->pure_st_max_dd_pts, r->pure_st_trades);
        }
        fclose(f_csv);
        printf("Saved grid_search_results.csv.\\n");
    }
    
    return 0;
}
