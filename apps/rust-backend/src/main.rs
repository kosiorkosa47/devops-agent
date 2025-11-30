use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use actix_cors::Cors;
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use std::env;

#[derive(Debug, Serialize, Deserialize)]
struct HealthResponse {
    status: String,
    service: String,
    version: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct MetricsResponse {
    cpu_usage: f64,
    memory_usage: f64,
    request_count: u64,
}

// Health check endpoint
async fn health() -> impl Responder {
    HttpResponse::Ok().json(HealthResponse {
        status: "healthy".to_string(),
        service: "rust-backend".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
}

// Performance-critical endpoint example
async fn process_data(data: web::Json<serde_json::Value>) -> impl Responder {
    // High-performance data processing here
    // This is where Rust shines for CPU-intensive tasks
    
    log::info!("Processing data: {:?}", data);
    
    HttpResponse::Ok().json(serde_json::json!({
        "status": "processed",
        "data": data.into_inner()
    }))
}

// Metrics endpoint for Prometheus
async fn metrics() -> impl Responder {
    // In production, use prometheus crate for real metrics
    HttpResponse::Ok().json(MetricsResponse {
        cpu_usage: 45.2,
        memory_usage: 512.0,
        request_count: 12345,
    })
}

// gRPC-like high-performance API endpoint
async fn grpc_handler(payload: web::Bytes) -> impl Responder {
    log::debug!("Received gRPC-style request: {} bytes", payload.len());
    
    // Process binary data with zero-copy when possible
    HttpResponse::Ok()
        .content_type("application/octet-stream")
        .body(payload)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize logging
    env_logger::init_from_env(env_logger::Env::new().default_filter_or("info"));
    
    // Load environment variables
    dotenv::dotenv().ok();
    
    let host = env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = env::var("PORT").unwrap_or_else(|_| "8080".to_string());
    let bind_address = format!("{}:{}", host, port);
    
    log::info!("Starting Rust backend server on {}", bind_address);
    
    // Optional: Database connection pool
    // let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    // let pool = PgPool::connect(&database_url).await.expect("Failed to connect to database");
    
    HttpServer::new(move || {
        // Configure CORS
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header()
            .max_age(3600);
        
        App::new()
            .wrap(cors)
            .wrap(actix_web::middleware::Logger::default())
            .route("/health", web::get().to(health))
            .route("/metrics", web::get().to(metrics))
            .route("/api/process", web::post().to(process_data))
            .route("/api/grpc", web::post().to(grpc_handler))
    })
    .bind(&bind_address)?
    .run()
    .await
}
