export class Office3DScene {
  constructor(containerEl) {
    this.container = containerEl;
    this.scene = new THREE.Scene();
    this.roomMeshes = {};
    this.agentMeshes = {};
    this.cars = [];
    this.cameraAngle = 0.78;
    this.cameraRadius = 31;
    this.lookAtTarget = new THREE.Vector3(0, 0.5, 0);

    const w = this.container.clientWidth;
    const h = this.container.clientHeight;

    this.camera = new THREE.PerspectiveCamera(40, w / h, 0.1, 180);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.08;
    this.container.appendChild(this.renderer.domElement);

    // Natural Sky & Sunlight
    this.hemiLight = new THREE.HemisphereLight(0xe0f2fe, 0x3f6212, 0.9);
    this.scene.add(this.hemiLight);

    this.sunLight = new THREE.DirectionalLight(0xfffbeb, 1.35);
    this.sunLight.position.set(24, 38, 22);
    this.sunLight.castShadow = true;
    this.sunLight.shadow.mapSize.width = 1024;
    this.sunLight.shadow.mapSize.height = 1024;
    this.sunLight.shadow.camera.near = 5;
    this.sunLight.shadow.camera.far = 95;
    const d = 24;
    this.sunLight.shadow.camera.left = -d;
    this.sunLight.shadow.camera.right = d;
    this.sunLight.shadow.camera.top = d;
    this.sunLight.shadow.camera.bottom = -d;
    this.sunLight.shadow.bias = -0.0005;
    this.scene.add(this.sunLight);

    this._buildCityEnvironment();
    this._buildCentralPlaza();
    this._spawnCityTrees();
    this._spawnTraffic();
  }

  _buildCityEnvironment() {
    // Lush manicured park & city block ground
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x4d7c3f,
      roughness: 0.92,
      metalness: 0.0
    });
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(140, 140), groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);

    // Concrete Plaza & Sidewalk Apron
    const sidewalkMat = new THREE.MeshStandardMaterial({
      color: 0xd6d3d1,
      roughness: 0.85,
      metalness: 0.05
    });
    const centralApron = new THREE.Mesh(new THREE.BoxGeometry(32, 0.06, 32), sidewalkMat);
    centralApron.position.y = 0.03;
    centralApron.receiveShadow = true;
    this.scene.add(centralApron);

    // Realistic Asphalt City Avenues (North-South & East-West Ring Roads)
    const asphaltMat = new THREE.MeshStandardMaterial({
      color: 0x27272a,
      roughness: 0.88,
      metalness: 0.08
    });

    const roadSpecs = [
      { w: 56, d: 3.4, x: 0, z: 16.5 },
      { w: 56, d: 3.4, x: 0, z: -16.5 },
      { w: 3.4, d: 56, x: 16.5, z: 0 },
      { w: 3.4, d: 56, x: -16.5, z: 0 }
    ];

    const lineMat = new THREE.MeshBasicMaterial({ color: 0xfef08a });

    roadSpecs.forEach((r) => {
      const road = new THREE.Mesh(new THREE.BoxGeometry(r.w, 0.08, r.d), asphaltMat);
      road.position.set(r.x, 0.04, r.z);
      road.receiveShadow = true;
      this.scene.add(road);

      // Dashed road centerline markings
      const isHorizontal = r.w > r.d;
      const count = 14;
      for (let i = -count / 2; i <= count / 2; i++) {
        if (Math.abs(i * 3.6) > 14.5 && Math.abs(i * 3.6) < 18.5) continue;
        const dash = new THREE.Mesh(
          new THREE.PlaneGeometry(isHorizontal ? 1.4 : 0.12, isHorizontal ? 0.12 : 1.4),
          lineMat
        );
        dash.rotation.x = -Math.PI / 2;
        dash.position.set(
          isHorizontal ? i * 3.6 : r.x,
          0.085,
          isHorizontal ? r.z : i * 3.6
        );
        this.scene.add(dash);
      }
    });
  }

  _buildCentralPlaza() {
    // Architectural Marble & Glass Headquarters Monument ("THE BRAIN" Campus Center)
    const marbleMat = new THREE.MeshStandardMaterial({ color: 0xf5f5f4, roughness: 0.35, metalness: 0.1 });
    const waterMat = new THREE.MeshStandardMaterial({ color: 0x0ea5e9, roughness: 0.15, metalness: 0.2 });
    const glassMat = new THREE.MeshPhysicalMaterial({
      color: 0xbae6fd,
      transparent: true,
      opacity: 0.65,
      roughness: 0.1,
      metalness: 0.1
    });

    // Circular Fountain Basin
    const basin = new THREE.Mesh(new THREE.CylinderGeometry(3.1, 3.3, 0.32, 36), marbleMat);
    basin.position.y = 0.16;
    basin.castShadow = true;
    basin.receiveShadow = true;
    this.scene.add(basin);

    const water = new THREE.Mesh(new THREE.CylinderGeometry(2.8, 2.8, 0.34, 36), waterMat);
    water.position.y = 0.17;
    this.scene.add(water);

    // Central Glass Obelisk / Data Pavilion
    const pavilion = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 1.15, 2.8, 24), glassMat);
    pavilion.position.y = 1.6;
    pavilion.castShadow = true;
    this.scene.add(pavilion);

    const roofCap = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 1.25, 0.18, 24), marbleMat);
    roofCap.position.y = 3.05;
    roofCap.castShadow = true;
    this.scene.add(roofCap);
  }

  _spawnCityTrees() {
    const trunkMat = new THREE.MeshStandardMaterial({ color: 0x5c4033, roughness: 0.9 });
    const leafMats = [
      new THREE.MeshStandardMaterial({ color: 0x2d6a4f, roughness: 0.8 }),
      new THREE.MeshStandardMaterial({ color: 0x40916c, roughness: 0.8 }),
      new THREE.MeshStandardMaterial({ color: 0x52b788, roughness: 0.8 })
    ];

    const treeCoords = [
      [-5.2, -5.2], [5.2, -5.2], [-5.2, 5.2], [5.2, 5.2],
      [-14.2, -14.2], [14.2, -14.2], [-14.2, 14.2], [14.2, 14.2],
      [-19.5, -10], [-19.5, 0], [-19.5, 10],
      [19.5, -10], [19.5, 0], [19.5, 10],
      [-10, -19.5], [0, -19.5], [10, -19.5],
      [-10, 19.5], [0, 19.5], [10, 19.5],
      [-6.5, -13.5], [6.5, -13.5], [-6.5, 13.5], [6.5, 13.5]
    ];

    treeCoords.forEach(([tx, tz], i) => {
      const tree = new THREE.Group();
      const scale = 0.85 + (i % 3) * 0.22;

      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.22, 1.3, 10), trunkMat);
      trunk.position.y = 0.65;
      trunk.castShadow = true;
      tree.add(trunk);

      const mat = leafMats[i % leafMats.length];
      const crown1 = new THREE.Mesh(new THREE.DodecahedronGeometry(0.95, 1), mat);
      crown1.position.set(0, 1.75, 0);
      crown1.castShadow = true;

      const crown2 = new THREE.Mesh(new THREE.DodecahedronGeometry(0.72, 1), mat);
      crown2.position.set(0.35, 2.25, 0.2);
      crown2.castShadow = true;

      tree.add(crown1, crown2);
      tree.scale.setScalar(scale);
      tree.position.set(tx, 0, tz);
      this.scene.add(tree);
    });
  }

  _spawnTraffic() {
    const carColors = [0xf8fafc, 0x1e293b, 0xb91c1c, 0x1d4ed8, 0xd97706, 0x475569];
    const glassMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.15, metalness: 0.8 });
    const wheelMat = new THREE.MeshStandardMaterial({ color: 0x18181b, roughness: 0.9 });

    const lanes = [
      { axis: 'x', fixed: 15.7, dir: 1, speed: 0.085, start: -24 },
      { axis: 'x', fixed: 17.3, dir: -1, speed: 0.075, start: 22 },
      { axis: 'x', fixed: -15.7, dir: 1, speed: 0.09, start: -10 },
      { axis: 'x', fixed: -17.3, dir: -1, speed: 0.08, start: 14 },
      { axis: 'z', fixed: 15.7, dir: -1, speed: 0.082, start: 20 },
      { axis: 'z', fixed: 17.3, dir: 1, speed: 0.078, start: -18 },
      { axis: 'z', fixed: -15.7, dir: -1, speed: 0.088, start: 8 },
      { axis: 'z', fixed: -17.3, dir: 1, speed: 0.072, start: -25 }
    ];

    lanes.forEach((lane, idx) => {
      const car = new THREE.Group();
      const bodyMat = new THREE.MeshStandardMaterial({
        color: carColors[idx % carColors.length],
        roughness: 0.25,
        metalness: 0.45
      });

      const chassis = new THREE.Mesh(new THREE.BoxGeometry(1.05, 0.42, 2.05), bodyMat);
      chassis.position.y = 0.34;
      chassis.castShadow = true;
      car.add(chassis);

      const cabin = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.36, 1.15), glassMat);
      cabin.position.set(0, 0.68, -0.08);
      cabin.castShadow = true;
      car.add(cabin);

      // 4 Wheels
      const wheelGeo = new THREE.CylinderGeometry(0.18, 0.18, 0.14, 12);
      wheelGeo.rotateZ(Math.PI / 2);
      [[-0.52, 0.62], [0.52, 0.62], [-0.52, -0.62], [0.52, -0.62]].forEach(([wx, wz]) => {
        const w = new THREE.Mesh(wheelGeo, wheelMat);
        w.position.set(wx, 0.18, wz);
        car.add(w);
      });

      if (lane.axis === 'x') {
        car.rotation.y = lane.dir > 0 ? Math.PI / 2 : -Math.PI / 2;
        car.position.set(lane.start, 0.08, lane.fixed);
      } else {
        car.rotation.y = lane.dir > 0 ? 0 : Math.PI;
        car.position.set(lane.fixed, 0.08, lane.start);
      }

      this.scene.add(car);
      this.cars.push({ mesh: car, ...lane });
    });
  }

  setLightingMood(mode) {
    if (mode === 'day') {
      this.scene.background = new THREE.Color(0xbae6fd);
      this.scene.fog = new THREE.FogExp2(0xbae6fd, 0.008);
      this.hemiLight.color.setHex(0xe0f2fe);
      this.hemiLight.intensity = 0.95;
      this.sunLight.color.setHex(0xfffbeb);
      this.sunLight.intensity = 1.35;
    } else if (mode === 'dusk') {
      this.scene.background = new THREE.Color(0xfed7aa);
      this.scene.fog = new THREE.FogExp2(0xfed7aa, 0.009);
      this.hemiLight.color.setHex(0xffedd5);
      this.hemiLight.intensity = 0.8;
      this.sunLight.color.setHex(0xf97316);
      this.sunLight.intensity = 1.25;
    } else {
      this.scene.background = new THREE.Color(0x1e293b);
      this.scene.fog = new THREE.FogExp2(0x1e293b, 0.01);
      this.hemiLight.color.setHex(0x94a3b8);
      this.hemiLight.intensity = 0.65;
      this.sunLight.color.setHex(0xcbd5e1);
      this.sunLight.intensity = 0.85;
    }
  }

  // Modern Glass & Timber Agency Studio Buildings
  createRoom(rm) {
    if (this.roomMeshes[rm.id]) return;
    const group = new THREE.Group();
    const roomW = 5.4;
    const roomD = 4.6;

    const concreteMat = new THREE.MeshStandardMaterial({ color: 0xe7e5e4, roughness: 0.75 });
    const timberMat = new THREE.MeshStandardMaterial({ color: 0x78350f, roughness: 0.65 });
    const glassWallMat = new THREE.MeshPhysicalMaterial({
      color: 0xf8fafc,
      transparent: true,
      opacity: 0.42,
      roughness: 0.1
    });
    const accentTrimMat = new THREE.MeshStandardMaterial({ color: rm.color, roughness: 0.35 });

    // Stone patio foundation
    const foundation = new THREE.Mesh(new THREE.BoxGeometry(roomW, 0.22, roomD), concreteMat);
    foundation.position.y = 0.11;
    foundation.receiveShadow = true;
    foundation.castShadow = true;
    group.add(foundation);

    // Subtle colored architectural trim band along base
    const trimBand = new THREE.Mesh(new THREE.BoxGeometry(roomW + 0.04, 0.08, roomD + 0.04), accentTrimMat);
    trimBand.position.y = 0.22;
    group.add(trimBand);

    // Glass Studio Walls (Back & Side)
    const backWall = new THREE.Mesh(new THREE.BoxGeometry(roomW, 1.85, 0.12), glassWallMat);
    backWall.position.set(0, 1.14, -roomD / 2 + 0.08);
    const sideWall = new THREE.Mesh(new THREE.BoxGeometry(0.12, 1.85, roomD), glassWallMat);
    sideWall.position.set(-roomW / 2 + 0.08, 1.14, 0);
    group.add(backWall, sideWall);

    // Warm Timber Roof Overhang (Cutaway top so you can see agents inside clearly)
    const backRoof = new THREE.Mesh(new THREE.BoxGeometry(roomW + 0.3, 0.14, 1.2), timberMat);
    backRoof.position.set(0, 2.1, -roomD / 2 + 0.5);
    backRoof.castShadow = true;
    group.add(backRoof);

    // Modern Oak Desks & Dual Monitors
    const deskMat = new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.55 });
    const monitorMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.25 });

    [-1.2, 1.1].forEach((dx) => {
      const desk = new THREE.Mesh(new THREE.BoxGeometry(1.45, 0.48, 0.72), deskMat);
      desk.position.set(dx, 0.45, -1.15);
      desk.castShadow = true;
      desk.receiveShadow = true;

      const monitor = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.44, 0.05), monitorMat);
      monitor.position.set(dx, 0.94, -1.32);
      monitor.castShadow = true;
      group.add(desk, monitor);
    });

    // Front Garden Courtyard / Sub-Agent Patio
    const patioMat = new THREE.MeshStandardMaterial({ color: 0xd6d3d1, roughness: 0.85 });
    const subPatio = new THREE.Mesh(new THREE.BoxGeometry(4.4, 0.04, 1.6), patioMat);
    subPatio.position.set(0, 0.23, 1.1);
    subPatio.receiveShadow = true;
    group.add(subPatio);

    // Paved Stone Walkway connecting Studio to Central Plaza
    const dist = Math.hypot(rm.x, rm.z);
    const walkway = new THREE.Mesh(
      new THREE.PlaneGeometry(0.95, dist),
      new THREE.MeshStandardMaterial({ color: 0xa8a29e, roughness: 0.9 })
    );
    walkway.rotation.x = -Math.PI / 2;
    walkway.rotation.z = -Math.atan2(rm.x, rm.z);
    walkway.position.set(rm.x / 2, 0.065, rm.z / 2);
    walkway.receiveShadow = true;
    this.scene.add(walkway);

    group.position.set(rm.x, 0, rm.z);
    this.scene.add(group);
    this.roomMeshes[rm.id] = group;
  }

  // Smooth, Natural Human-Proportioned Agency Specialists
  ensureAgent(ag, roomsMap) {
    if (this.agentMeshes[ag.id]) return this.agentMeshes[ag.id];
    const root = new THREE.Group();

    const jacketMat = new THREE.MeshStandardMaterial({ color: ag.color || '#2563eb', roughness: 0.65 });
    const slacksMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.75 });
    const skinMat = new THREE.MeshStandardMaterial({ color: 0x8d5524, roughness: 0.55 });
    const hairMat = new THREE.MeshStandardMaterial({ color: 0x18181b, roughness: 0.85 });

    // Legs
    const leftLeg = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.065, 0.46, 12), slacksMat);
    leftLeg.position.set(-0.1, 0.23, 0);
    leftLeg.castShadow = true;

    const rightLeg = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.065, 0.46, 12), slacksMat);
    rightLeg.position.set(0.1, 0.23, 0);
    rightLeg.castShadow = true;

    // Smooth Blazer Torso
    const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.19, 0.17, 0.52, 16), jacketMat);
    torso.position.y = 0.7;
    torso.castShadow = true;

    // Shoulders & Arms
    const leftArm = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.05, 0.44, 10), jacketMat);
    leftArm.position.set(-0.24, 0.68, 0.06);
    leftArm.rotation.x = -0.35;
    leftArm.castShadow = true;

    const rightArm = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.05, 0.44, 10), jacketMat);
    rightArm.position.set(0.24, 0.68, 0.06);
    rightArm.rotation.x = -0.35;
    rightArm.castShadow = true;

    // Smooth Head & Hair
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.19, 20, 20), skinMat);
    head.position.y = 1.15;
    head.castShadow = true;

    const hair = new THREE.Mesh(
      new THREE.SphereGeometry(0.198, 20, 16, 0, Math.PI * 2, 0, Math.PI * 0.52),
      hairMat
    );
    hair.position.y = 1.17;

    root.add(leftLeg, rightLeg, torso, leftArm, rightArm, head, hair);

    const rm = roomsMap[ag.room] || { x: 0, z: 0 };
    const offsetIdx = Object.keys(this.agentMeshes).length % 4;
    const slotX = ag.is_subagent ? ((ag.slot || 0) - 1) * 1.35 : (offsetIdx % 2 === 0 ? -1.15 : 1.05);
    const slotZ = ag.is_subagent ? 1.1 : -0.45;
    root.position.set(rm.x + slotX, 0.22, rm.z + slotZ);

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

    const camH = this.cameraRadius * 0.62;
    this.camera.position.x = this.lookAtTarget.x + Math.sin(this.cameraAngle) * this.cameraRadius;
    this.camera.position.z = this.lookAtTarget.z + Math.cos(this.cameraAngle) * this.cameraRadius;
    this.camera.position.y = camH;
    this.camera.lookAt(this.lookAtTarget);

    // Move city cars smoothly along avenues
    for (const c of this.cars) {
      if (c.axis === 'x') {
        c.mesh.position.x += c.dir * c.speed;
        if (c.dir > 0 && c.mesh.position.x > 27) c.mesh.position.x = -27;
        if (c.dir < 0 && c.mesh.position.x < -27) c.mesh.position.x = 27;
      } else {
        c.mesh.position.z += c.dir * c.speed;
        if (c.dir > 0 && c.mesh.position.z > 27) c.mesh.position.z = -27;
        if (c.dir < 0 && c.mesh.position.z < -27) c.mesh.position.z = 27;
      }
    }

    // Subtle natural breathing & working posture for agents
    for (const [id, ag] of Object.entries(agentsMap)) {
      const mesh = this.agentMeshes[id];
      if (!mesh) continue;
      const rm = roomsMap[ag.room];
      if (rm && !ag.is_subagent) {
        const targetX = rm.x + (id.length % 2 === 0 ? -1.15 : 1.05);
        const targetZ = rm.z - 0.45;
        mesh.position.x += (targetX - mesh.position.x) * 0.05;
        mesh.position.z += (targetZ - mesh.position.z) * 0.05;
      }
      mesh.position.y = ag.state === 'working'
        ? 0.22 + Math.abs(Math.sin(now * 0.008)) * 0.035
        : 0.22 + Math.sin(now * 0.003) * 0.015;
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
      pos.y += 2.4;
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
      pos.y += 1.65;
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