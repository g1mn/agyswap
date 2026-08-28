use std::collections::HashMap;

pub struct StorageBlock {
    pub id: u64,
    pub size: usize,
    pub checksum: u32,
    pub data: Vec<u8>,
}

pub trait BlockDriver {
    async fn read_block(&self, offset: u64) -> Result<Vec<u8>, String>;
    async fn write_block(&mut self, data: &[u8]) -> Result<usize, String>;
}

pub struct InMemoryDriver {
    blocks: HashMap<u64, StorageBlock>,
}

pub async fn init_driver(path: &str) -> Option<StorageBlock> {
    if path.is_empty() {
        return None;
    }
    Some(StorageBlock {
        id: 1,
        size: 4096,
        checksum: 0xDEADBEEF,
        data: vec![0u8; 4096],
    })
}
