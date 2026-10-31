# SENSEFORGE: Measurement DSL Grammar Specification

**Version:** 0.1.0  
**Grammar ID:** `senseforge.dsl.v1`  
**Authors:** SENSEFORGE Principal Research Architecture Group  

---

## 1. Formal Grammar in Extended Backus-Naur Form (EBNF)

```ebnf
Expression         ::= SeriesExpression | ScalarExpression ;

SeriesExpression   ::= ChannelTerminal
                     | SeriesUnaryOp
                     | SeriesBinaryOp ;

ScalarExpression   ::= ConstantTerminal
                     | SeriesCollapseOp
                     | BivariateCollapseOp
                     | ScalarBinaryOp ;

(* Terminals *)
ChannelTerminal    ::= "Channel(" Integer ")" ;
ConstantTerminal   ::= "Const(" Float ")" ;

(* Series Preserving Unary / Temporal Operations *)
SeriesUnaryOp      ::= "Diff(" SeriesExpression [ "," Integer ] ")"
                     | "Lag(" SeriesExpression [ "," Integer ] ")"
                     | "RollingMean(" SeriesExpression [ "," Integer ] ")"
                     | "RollingVar(" SeriesExpression [ "," Integer ] ")"
                     | "Abs(" SeriesExpression ")"
                     | "Tanh(" SeriesExpression ")"
                     | "Sigmoid(" SeriesExpression ")"
                     | "Clip(" SeriesExpression "," Float "," Float ")" ;

(* Window Collapsing Operations *)
SeriesCollapseOp   ::= "Mean(" SeriesExpression ")"
                     | "Variance(" SeriesExpression ")" ;

(* Bivariate Series Collapsing Operations *)
BivariateCollapseOp::= "Covariance(" SeriesExpression "," SeriesExpression ")"
                     | "Correlation(" SeriesExpression "," SeriesExpression ")" ;

(* Binary Arithmetic with Type Broadcasting *)
SeriesBinaryOp     ::= "Add(" SeriesExpression "," SeriesExpression ")"
                     | "Add(" SeriesExpression "," ScalarExpression ")"
                     | "Add(" ScalarExpression "," SeriesExpression ")"
                     | "Sub(" SeriesExpression "," SeriesExpression ")"
                     | "Sub(" SeriesExpression "," ScalarExpression ")"
                     | "Sub(" ScalarExpression "," SeriesExpression ")"
                     | "Mul(" SeriesExpression "," SeriesExpression ")"
                     | "Mul(" SeriesExpression "," ScalarExpression ")"
                     | "Mul(" ScalarExpression "," SeriesExpression ")"
                     | "DivSafe(" SeriesExpression "," SeriesExpression ")"
                     | "DivSafe(" SeriesExpression "," ScalarExpression ")"
                     | "DivSafe(" ScalarExpression "," SeriesExpression ")" ;

ScalarBinaryOp     ::= "Add(" ScalarExpression "," ScalarExpression ")"
                     | "Sub(" ScalarExpression "," ScalarExpression ")"
                     | "Mul(" ScalarExpression "," ScalarExpression ")"
                     | "DivSafe(" ScalarExpression "," ScalarExpression ")" ;

Integer            ::= [0-9]+ ;
Float              ::= ["-"] [0-9]+ ["." [0-9]+] ;
```

---

## 2. Mathematical Semantics of Primitive Operators

| Operator | Arity | Input Types | Output Type | Mathematical Definition |
| :--- | :--- | :--- | :--- | :--- |
| `Channel(i)` | 0 | None | $\text{SERIES}$ | $y_t^{(i)}$ for $t \in [0, T]$ |
| `Const(c)` | 0 | None | $\text{SCALAR}$ | $c \in \mathbb{R}$ |
| `Diff(x, tau)` | 1 | $\text{SERIES}$ | $\text{SERIES}$ | $x_t - x_{t-\tau}$ (zero padded for $t < \tau$) |
| `Lag(x, tau)` | 1 | $\text{SERIES}$ | $\text{SERIES}$ | $x_{t-\tau}$ (initial value clamped for $t < \tau$) |
| `RollingMean(x, w)` | 1 | $\text{SERIES}$ | $\text{SERIES}$ | $\frac{1}{\min(t+1, w)} \sum_{k=0}^{\min(t, w-1)} x_{t-k}$ |
| `RollingVar(x, w)` | 1 | $\text{SERIES}$ | $\text{SERIES}$ | $\mathbb{E}[x^2]_w - (\mathbb{E}[x]_w)^2$ |
| `Mean(x)` | 1 | $\text{SERIES}$ | $\text{SCALAR}$ | $\frac{1}{T} \sum_{t=1}^T x_t$ |
| `Variance(x)` | 1 | $\text{SERIES}$ | $\text{SCALAR}$ | $\frac{1}{T} \sum_{t=1}^T (x_t - \bar{x})^2$ |
| `Covariance(x, y)` | 2 | $\text{SERIES} \times \text{SERIES}$ | $\text{SCALAR}$ | $\frac{1}{T-1} \sum_{t=1}^T (x_t - \bar{x})(y_t - \bar{y})$ |
| `Correlation(x, y)`| 2 | $\text{SERIES} \times \text{SERIES}$ | $\text{SCALAR}$ | $\frac{\text{Cov}(x, y)}{\sqrt{\text{Var}(x)\text{Var}(y) + \epsilon}}$ |
| `DivSafe(x, y)` | 2 | Any | Broadcast | $\frac{x}{y + \text{sign}(y)\cdot 10^{-6}}$ |
| `Tanh(x)` | 1 | Any | Same | $\tanh(x)$ elementwise |
| `Sigmoid(x)` | 1 | Any | Same | $\frac{1}{1 + e^{-\text{clip}(x, -50, 50)}}$ elementwise |

