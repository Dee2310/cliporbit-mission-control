export class Office3DScene {
  constructor(containerEl) {
    this.container = containerEl;
    this.scene = new THREE.Scene();
    this.roomMeshes = {};
    this.agentMeshes = {};
    this.cameraAngle = 0.72;
    this.cameraRadius = 29;
    this.lookAtTarget = new THREE.Vector3(0, 0.5, 0);

    const w = this.container.clientWidth;
    const h = this.container.clientHeight;

    this.camera = new THREE.PerspectiveCamera(42, w / h, 0.1, 140);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'low-power' });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.container.appendChild(this.renderer.domElement);

    this.ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    this.scene.add(this.ambientLight);

    this.keyLight = new THREE.DirectionalLight(0xffffff, 1.0);
    this.keyLight.position.set(16, 28, 16);
    this.scene.add(this.keyLight);

    this.scene.add(new THREE.GridHelper(44, 44, 0x1e293b, 0x111827));
    this._buildCentralBrain();
  }

  _buildCentralBrain() {
    const brainBase = new THREE.Mesh(
      new THREE.CylinderGeometry(2.6, 3.0, 0.25, 36),
      new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.3, metalness: 0.7 })
    );
    brainBase.position.y = 0.12;
    this.scene.add(brainBase);

    const brainGlowRing = new THREE.Mesh(
      new THREE.RingGeometry(2.65, 2.85, 48),
      new THREE.MeshBasicMaterial({ color: 0x38bdf8, side: THREE.DoubleSide })
    );
    brainGlowRing.rotation.x = Math.PI / 2;
    brainGlowRing.position.y = 0.26;
    this.scene.add(brainGlowRing);

    const beam = new THREE.Mesh(
      new THREE.CylinderGeometry(0.12, 0.28, 3.6, 16),
      new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.35 })
    );
    beam.position.y = 1.9;
    this.scene.add(beam);

    this.brainSphere = new THREE.Mesh(
      new THREE.SphereGeometry(0.68, 24, 24),
      new THREE.MeshStandardMaterial({
        color: 0x7dd3fc,
        emissive: 0x0284c7,
        emissiveIntensity: 0.75,
        roughness: 0.2
      })
    );
    this.brainSphere.position.y = 2.1;
    this.scene.add(this.brainSphere);

    this.brainRing1 = new THREE.Mesh(
      new THREE.TorusGeometry(1.15, 0.025, 10, 40),
      new THREE.MeshBasicMaterial({ color: 0x38bdf8 })
    );
    this.brainRing1.position.y = 2.1;
    this.brainRing1.rotation.x = 0.7;
    this.scene.add(this.brainRing1);

    this.brainRing2 = new THREE.Mesh(
      new THREE.TorusGeometry(1.4, 0.02, 10, 40),
      new THREE.MeshBasicMaterial({ color: 0xa78bfa })
    );
    this.brainRing2.position.y = 2.1;
    this.brainRing2.rotation.y = 0.9;
    this.scene.add(this.brainRing2);
  }

  setLightingMood(mode) {
    if (mode === 'day') {
      this.scene.background = new THREE.Color(0x131929);
      this.ambientLight.color.setHex(0xffffff);
      this.ambientLight.intensity = 1.05;
      this.keyLight.color.setHex(0xfffbeb);
    } else if (mode === 'dusk') {
      this.scene.background = new THREE.Color(0x161124);
      this.ambientLight.color.setHex(0xfde68a);
      this.ambientLight.intensity = 0.85;
      this.keyLight.color.setHex(0xfb923c);
    } else {
      this.scene.background = new THREE.Color(0x090c14);
      this.ambientLight.color.setHex(0xcbd5e1);
      this.ambientLight.intensity = 0.7;
      this.keyLight.color.setHex(0x60a5fa);
    }
  }

  createRoom(rm) {
    if (this.roomMeshes[rm.id]) return;
    const group = new THREE.Group();
    const roomW = 5.4;
    const roomD = 4.6;

    const floor = new THREE.Mesh(
      new THREE.BoxGeometry(roomW, 0.18, roomD),
      new THREE.MeshStandardMaterial({ color: rm.floor || 0x1e1b4b, roughness: 0.5 })
    );
    floor.position.y = 0.09;
    group.add(floor);

    const border = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(roomW + 0.05, 0.2, roomD + 0.05)),
      new THREE.LineBasicMaterial({ color: rm.color })
    );
    border.position.y = 0.1;
    group.add(border);

    const wallMat = new THREE.MeshStandardMaterial({
      color: rm.color,
      transparent: true,
      opacity: 0.28,
      roughness: 0.4
    });
    const backWall = new THREE.Mesh(new THREE.BoxGeometry(roomW, 1.35, 0.14), wallMat);
    backWall.position.set(0, 0.76, -roomD / 2 + 0.07);
    const sideWall = new THREE.Mesh(new THREE.BoxGeometry(0.14, 1.35, roomD), wallMat);
    sideWall.position.set(-roomW / 2 + 0.07, 0.76, 0);
    group.add(backWall, sideWall);

    const deskMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.3 });
    const screenMat = new THREE.MeshBasicMaterial({ color: rm.color });

    [-1.2, 1.1].forEach((dx) => {
      const desk = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.45, 0.7), deskMat);
      desk.position.set(dx, 0.4, -1.2);
      const monitor = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.42, 0.06), screenMat);
      monitor.position.set(dx, 0.88, -1.35);
      group.add(desk, monitor);
    });

    const subBayBorder = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(4.4, 0.02, 1.7)),
      new THREE.LineBasicMaterial({ color: rm.color, transparent: true, opacity: 0.65 })
    );
    subBayBorder.position.set(0, 0.2, 1.05);
    group.add(subBayBorder);

    const dist = Math.hypot(rm.x, rm.z);
    const conduit = new THREE.Mesh(
      new THREE.PlaneGeometry(0.12, dist),
      new THREE.MeshBasicMaterial({ color: rm.color, side: THREE.DoubleSide, transparent: true, opacity: 0.55 })
    );
    conduit.rotation.x = Math.PI / 2;
    conduit.rotation.z = -Math.atan2(rm.x, rm.z);
    conduit.position.set(rm.x / 2, 0.02, rm.z / 2);
    this.scene.add(conduit);

    group.position.set(rm.x, 0, rm.z);
    this.scene.add(group);
    this.roomMeshes[rm.id] = group;
  }

  ensureAgent(ag, roomsMap) {
    if (this.agentMeshes[ag.id]) return this.agentMeshes[ag.id];
    const root = new THREE.Group();
    const outfitMat = new THREE.MeshStandardMaterial({ color: ag.color || '#38bdf8', roughness: 0.35 });
    const skinMat = new THREE.MeshStandardMaterial({ color: 0xfde68a, roughness: 0.4 });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.5 });

    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.26, 0.55, 14), outfitMat);
    body.position.y = 0.55;
    root.add(body);

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.24, 16, 16), skinMat);
    head.position.y = 1.02;
    root.add(head);

    const visor = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.1, 0.14), darkMat);
    visor.position.set(0, 1.03, 0.17);
    root.add(visor);

    if (ag.is_subagent) {
      const halo = new THREE.Mesh(
        new THREE.TorusGeometry(0.34, 0.025, 8, 24),
        new THREE.MeshBasicMaterial({ color: ag.color })
      );
      halo.rotation.x = Math.PI / 2;
      halo.position.y = 0.22;
      root.add(halo);
    }

    const rm = roomsMap[ag.room] || { x: 0, z: 0 };
    const offsetIdx = Object.keys(this.agentMeshes).length % 4;
    const slotX = ag.is_subagent ? ((ag.slot || 0) - 1) * 1.35 : (offsetIdx % 2 === 0 ? -1.1 : 1.0);
    const slotZ = ag.is_subagent ? 1.05 : -0.45;
    root.position.set(rm.x + slotX, 0.18, rm.z + slotZ);

    this.scene.add(root);
    this.agentMeshes[ag.id] = root;
    return root;
  }

  renderFrame(now, selectedRoom, roomsMap, agentsMap) {
    const desiredLook = new THREE.Vector3(0, 0.6, 0);
    if (selectedRoom) {
      desiredLook.set(selectedRoom.x, 0.8, selectedRoom.z);
    }
    this.lookAtTarget.lerp(desiredLook, 0.08);

    const camH = this.cameraRadius * 0.65;
    this.camera.position.x = this.lookAtTarget.x + Math.sin(this.cameraAngle) * this.cameraRadius;
    this.camera.position.z = this.lookAtTarget.z + Math.cos(this.cameraAngle) * this.cameraRadius;
    this.camera.position.y = camH;
    this.camera.lookAt(this.lookAtTarget);

    if (this.brainSphere) {
      this.brainSphere.position.y = 2.1 + Math.sin(now * 0.003) * 0.12;
      this.brainRing1.rotation.z = now * 0.0015;
      this.brainRing2.rotation.x = -now * 0.0012;
    }

    for (const [id, ag] of Object.entries(agentsMap)) {
      const mesh = this.agentMeshes[id];
      if (!mesh) continue;
      const rm = roomsMap[ag.room];
      if (rm && !ag.is_subagent) {
        const targetX = rm.x + (id.length % 2 === 0 ? -1.1 : 1.0);
        const targetZ = rm.z - 0.45;
        mesh.position.x += (targetX - mesh.position.x) * 0.05;
        mesh.position.z += (targetZ - mesh.position.z) * 0.05;
      }
      mesh.position.y = ag.state === 'working'
        ? 0.18 + Math.abs(Math.sin(now * 0.014)) * 0.08
        : 0.18 + Math.sin(now * 0.004) * 0.02;
    }

    this.renderer.render(this.scene, this.camera);
  }

  projectLabels(roomsMap, agentsMap) {
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    const roomTags = [];
    const agentPills = [];

    for (const rm of Object.values(roomsMap)) {
      const mesh = this.roomMeshes[rm.id];
      if (!mesh) continue;
      const pos = mesh.position.clone();
      pos.y += 2.2;
      pos.project(this.camera);
      if (pos.z < 1) {
        const roomAgents = Object.values(agentsMap).filter((a) => a.room === rm.id);
        roomTags.push({
          id: rm.id,
          name: rm.name,
          color: rm.color,
          agentCount: roomAgents.length,
          runningCount: roomAgents.filter((a) => a.state === 'working').length,
          x: (pos.x * 0.5 + 0.5) * w,
          y: (-(pos.y * 0.5) + 0.5) * h
        });
      }
    }

    for (const ag of Object.values(agentsMap)) {
      const mesh = this.agentMeshes[ag.id];
      if (!mesh) continue;
      const pos = mesh.position.clone();
      pos.y += 1.5;
      pos.project(this.camera);
      if (pos.z < 1) {
        agentPills.push({
          id: ag.id,
          name: ag.state === 'working' ? `${ag.name} (${ag.progress}%)` : ag.name,
          color: ag.color,
          x: (pos.x * 0.5 + 0.5) * w,
          y: (-(pos.y * 0.5) + 0.5) * h
        });
      }
    }

    return { roomTags, agentPills };
  }

  resize() {
    if (!this.container) return;
    this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
  }
}