use std::{fs, io::Write};
fn run() -> std::io::Result<()> {
    println!("errno address {:p}", unsafe { errno_ptr() });
    let root = "/AROS/LCrustProbe";
    fs::create_dir_all(root)?;
    for n in 0..3 {
        let tmp = format!("{root}/stage");
        let dest = format!("{root}/dest");
        let _ = fs::remove_file(&tmp);
        let mut f = fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&tmp)?;
        println!("{n} write {:?}", f.write_all(b"hello"));
        println!("{n} sync {:?}", f.sync_all());
        drop(f);
        println!("{n} rename {:?}", fs::rename(&tmp, &dest));
        let f = fs::OpenOptions::new()
            .write(true)
            .append(true)
            .open(&dest)?;
        println!("{n} truncate {:?}", f.set_len(0));
        println!("{n} sync-data {:?}", f.sync_data());
    }
    fs::copy(
        "/AROS/LCinput/Fixtures/sample.png",
        format!("{root}/zażółć.png"),
    )?;
    println!(
        "UTF8 file exists {}",
        fs::metadata(format!("{root}/zażółć.png")).is_ok()
    );
    Ok(())
}
unsafe extern "C" {
    #[link_name = "___geterrnoptr"]
    fn errno_ptr() -> *mut i32;
}
fn concurrent() -> bool {
    let dir_error = fs::File::create("/AROS/LCrustProbe").unwrap_err().kind();
    println!("directory error baseline {dir_error:?}");
    std::thread::scope(|scope| {
        let mut jobs = Vec::new();
        for t in 0..4 {
            jobs.push(scope.spawn(move || {
                for n in 0..100 {
                    let path = format!("/AROS/LCrustProbe/thread-{t}-{n}");
                    let temp = format!("{path}.tmp");
                    let data = vec![b'A' + t; 4096];
                    let mut f = fs::OpenOptions::new()
                        .write(true)
                        .create(true)
                        .truncate(true)
                        .open(&temp)
                        .unwrap();
                    f.write_all(&data).unwrap();
                    f.sync_all().unwrap();
                    drop(f);
                    fs::rename(&temp, &path).unwrap();
                    let actual = fs::read(&path).unwrap();
                    let e =
                        fs::File::open(format!("/AROS/LCrustProbe/missing-{t}-{n}")).unwrap_err();
                    assert_eq!(e.kind(), std::io::ErrorKind::NotFound, "missing file: {e}");
                    let e = fs::File::create("/AROS/LCrustProbe").unwrap_err();
                    assert_eq!(e.kind(), dir_error, "directory write: {e}");
                    assert!(
                        actual == data,
                        "wrong file bytes: thread {t} iteration {n}, length {}",
                        actual.len()
                    );
                    fs::remove_file(path).unwrap();
                }
            }));
        }
        let mut ok = true;
        for job in jobs {
            let r = job.join();
            ok &= r.is_ok();
            println!("concurrent {r:?}");
        }
        ok
    })
}
fn cross_thread() -> bool {
    let path = "/AROS/LCrustProbe/cross";
    let mut f = fs::File::create(path).unwrap();
    let job = std::thread::spawn(move || {
        println!("cross-write {:?}", f.write_all(b"owned-main-written-child"));
        println!("cross-sync {:?}", f.sync_all());
    });
    let joined = job.join();
    let data = fs::read(path);
    println!("cross-join {joined:?}; data {data:?}");
    joined.is_ok() && data.is_ok_and(|b| b == b"owned-main-written-child")
}
fn main() -> std::process::ExitCode {
    println!("cwd normalization {:?}", std::env::set_current_dir("."));
    println!("main {:?}", run());
    println!("thread {:?}", std::thread::spawn(run).join());
    let parallel = concurrent();
    let cross = cross_thread();
    if parallel && cross {
        std::process::ExitCode::SUCCESS
    } else {
        std::process::ExitCode::FAILURE
    }
}
