# Open-Source Deployment Strategy: Self-Managed Cloud VM Approach (AWS/Azure)

## Overview
This deployment strategy uses a self-managed cloud VM (such as AWS EC2 or Azure VM) with open-source components. This approach eliminates managed cloud service costs while providing enterprise-grade performance and reliability for multi-million record datasets. You retain full control over your stack, running on a cloud VM you manage yourself.

> **Note:** While AWS and Azure both offer managed hosting options (e.g., RDS, Azure Database, managed Kubernetes), this guide focuses on the self-managed VM pattern for maximum cost savings, flexibility, and portability. If you prefer managed services, consult the respective cloud provider's documentation for those options.

## Cost Analysis: Self-Managed Cloud vs Managed Services

### **Cost Comparison**

| Component | AWS Managed (RDS, etc.) | Azure Managed | **Self-Managed AWS EC2** | **Self-Managed Azure VM** |
|-----------|-------------------------|---------------|--------------------------|--------------------------|
| **Database (1M records)** | $150/month | $176/month | $40–$80/month | $40–$80/month |
| **Compute (1M records)** | $60/month | $65/month | included above | included above |
| **Storage (1M records)** | $10/month | $6/month | included above | included above |
| **Monitoring** | $10/month | $15/month | $0 (self-managed) | $0 (self-managed) |
| **Total Monthly** | $230/month | $262/month | **$40–$80/month** | **$40–$80/month** |

**Annual Savings**: $2,280+ vs managed services

### **Example Instance Types and Costs (as of 2024)**
- **AWS EC2 t3.xlarge (4 vCPU, 16GB RAM):** ~$50/month (on-demand, Linux, us-east-1)
- **AWS EC2 m5.2xlarge (8 vCPU, 32GB RAM):** ~$150/month (on-demand)
- **Azure D4as v5 (4 vCPU, 16GB RAM):** ~$60/month (on-demand)
- **Azure D8as v5 (8 vCPU, 32GB RAM):** ~$120/month (on-demand)
- **Storage:** EBS or Azure Disk, ~$0.10/GB/month
- **Elastic IP (AWS):** $3–$4/month if not always attached

> **Tip:** Use reserved or spot instances for further savings.

---

## Architecture Design

### **Open-Source Stack (Cloud VM)**
- **Database Layer:** PostgreSQL 15 with pgvector (installed on your VM)
- **Application Layer:** Docker Compose for API, frontend, enrichment, monitoring
- **Storage Layer:** Cloud block storage (EBS, Azure Disk)
- **Backup:** pg_dump, EBS/Azure Disk snapshots
- **Monitoring:** Prometheus, Grafana (self-managed)

---

## Cloud VM Deployment Steps

### 1. Launch Cloud VM
- **AWS:** EC2 instance (Ubuntu 22.04 LTS recommended)
- **Azure:** Virtual Machine (Ubuntu 22.04 LTS recommended)
- Choose instance type based on dataset size (see above)
- Attach block storage (EBS/Azure Disk) for database/data
- Assign Elastic IP (AWS) or static public IP (Azure)
- Add your SSH key pair

### 2. Configure Security
- **AWS:** Security Groups (open only required ports: 22, 80, 443, 5001, 8050, 3000)
- **Azure:** Network Security Groups (same ports)
- Restrict access to trusted IPs where possible

### 3. Prepare the VM
- SSH in: `ssh -i your-key.pem ubuntu@your-elastic-ip`
- Update system: `sudo apt update && sudo apt upgrade -y`
- (Optional) Mount and format additional storage for /opt/doctrove or /var/lib/postgresql

### 4. Install and Configure Stack
- Install Docker, Docker Compose, PostgreSQL, pgvector (see open-source guide)
- Use block storage for database/data directories for persistence
- Set up Docker Compose for API, frontend, enrichment, monitoring

### 5. Backups and Snapshots
- Use both `pg_dump` and EBS/Azure Disk snapshots for robust backup strategy
- Consider automating snapshots with AWS Lambda, Azure Automation, or Data Lifecycle Manager

### 6. SSL and DNS
- Use Certbot for SSL as described above
- Point your domain to the Elastic IP or static public IP

### 7. Monitoring and Scaling
- Use CloudWatch (AWS) or Azure Monitor (optional)
- Resize your instance or add storage as your needs grow

---

## AWS and Azure-Specific Tips
- **Performance:** Use EBS-optimized (AWS) or Premium Disk (Azure) for best disk I/O
- **Persistence:** Always use block storage for database/data, not ephemeral instance storage
- **Security:** Use Security Groups/NSGs and IAM roles for least-privilege access
- **Cost:** Monitor instance and storage costs; shut down or resize when not needed
- **Snapshots:** Regularly snapshot block storage for disaster recovery

---

## Managed Service Alternatives (Briefly)
- **AWS RDS, Azure Database, etc.:** Provide managed PostgreSQL, backups, failover, and patching, but at higher cost and with less control.
- **When to use:** If you want minimal maintenance and are willing to pay more for built-in HA, backups, and scaling.
- **This guide focuses on:** Self-managed VMs for maximum control and cost savings.

---

## Disaster Recovery, Maintenance, and Operations
(Sections on backup, monitoring, and maintenance apply as written—just use cloud block storage and snapshot tools.)

---

## Benefits of Self-Managed Cloud VM Approach
- **Cost-effective:** Lower monthly cost than managed services or physical hardware
- **Full control:** Root/admin access, custom configuration, no vendor lock-in
- **Portability:** Easily migrate to another provider or region
- **Scalability:** Resize VM or storage as needed
- **No hardware to buy or maintain:** All infrastructure is virtual

---

## Implementation Timeline
(Use the same week-by-week plan, but all steps are performed on your cloud VM.)

---

*This guide is now streamlined for cloud VM (AWS/Azure) self-managed deployment. Physical server purchase and hosting are no longer recommended or described.* 