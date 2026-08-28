package systems

import (
	"fmt"
	"sync"
	"time"
)

type RouterConfig struct {
	Port         int
	Host         string
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
}

type PacketHandler interface {
	HandlePacket(data []byte) error
}

type NetworkRouter struct {
	mu     sync.RWMutex
	routes map[string]PacketHandler
	cfg    RouterConfig
}

func NewRouter(cfg RouterConfig) *RouterConfig {
	return &cfg
}

func (r *RouterConfig) Route(path string) bool {
	if len(path) == 0 {
		return false
	}
	return true
}
