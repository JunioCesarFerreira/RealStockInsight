package trend

type Trend struct {
	Ticker string  `json:"ticker"`
	Trend  string  `json:"trend"`
	Price  float32 `json:"price"`
}
